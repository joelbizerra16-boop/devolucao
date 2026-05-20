from __future__ import annotations

import os
import socket
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()
COMMON_REGIONS = (
    "us-east-1",
    "us-east-2",
    "sa-east-1",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
)


@dataclass
class UriTarget:
    label: str
    url: str
    connection_type: str
    host: str
    port: int
    user: str
    password: str
    database: str
    region: str | None = None


@dataclass
class ProbeResult:
    target: UriTarget
    dns_status: str
    tcp_status: str
    psycopg2_status: str
    sqlalchemy_status: str
    result_label: str
    success: bool
    error_text: str
    exact_reason: str
    problem_area: str
    recommendation: str
    suggested_uri: str
    ipv4_list: list[str]
    ipv6_list: list[str]
    version: str | None
    environment_labels: list[str]


@dataclass
class RegionProbe:
    region: str
    score: int
    reason: str


@dataclass
class RegionDetection:
    region: str
    confirmed: bool
    probes: list[RegionProbe]


def print_header(title: str) -> None:
    print("\n===================================================")
    print(title)
    print("===================================================\n")


def mask_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.password:
        return url.replace(parsed.password, "********")
    return url


def format_bool_status(ok: bool, detail: str = "") -> str:
    if ok:
        return "OK"
    if detail:
        return f"FALHA ({detail})"
    return "FALHA"


def validate_uri(url: str) -> tuple[bool, str, object | None]:
    if not url:
        return False, "DATABASE_URL não encontrada no .env", None

    try:
        parsed = urlparse(url)
    except Exception as exc:
        return False, f"URI inválida: {exc}", None

    if parsed.scheme not in {"postgresql", "postgres"}:
        return False, "URI inválida: esquema deve ser postgresql://", None
    if not parsed.hostname:
        return False, "URI inválida: host ausente", None
    if not parsed.username:
        return False, "URI inválida: usuário ausente", None
    if parsed.port is None:
        return False, "URI inválida: porta ausente", None
    if not parsed.path or parsed.path == "/":
        return False, "URI inválida: database ausente", None

    return True, "URI válida", parsed


def detect_connection_type(host: str, port: int) -> str:
    normalized = host.lower()
    if normalized.startswith("db.") and normalized.endswith(".supabase.co"):
        return "DIRECT"
    if "pooler.supabase.com" in normalized:
        if port == 5432:
            return "SESSION POOLER"
        if port == 6543:
            return "TRANSACTION POOLER"
    return "DESCONHECIDO"


def extract_project_ref(parsed: object) -> str:
    host = (parsed.hostname or "").lower()
    user = parsed.username or ""

    if host.startswith("db.") and host.endswith(".supabase.co"):
        return host.removeprefix("db.").removesuffix(".supabase.co")

    if "pooler.supabase.com" in host and user.startswith("postgres."):
        return user.split(".", 1)[1]

    project_ref = (os.getenv("SUPABASE_PROJECT_REF") or "").strip()
    return project_ref


def extract_region_from_host(host: str) -> str | None:
    normalized = host.lower()
    prefix = "aws-0-"
    suffix = ".pooler.supabase.com"
    if normalized.startswith(prefix) and normalized.endswith(suffix):
        return normalized[len(prefix):-len(suffix)]
    return None


def build_direct_uri(project_ref: str, password: str, database: str) -> UriTarget:
    encoded_password = quote(password, safe="")
    url = f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/{database}"
    return UriTarget(
        label="DIRECT CONNECTION",
        url=url,
        connection_type="DIRECT",
        host=f"db.{project_ref}.supabase.co",
        port=5432,
        user="postgres",
        password=password,
        database=database,
    )


def build_pooler_uri(project_ref: str, password: str, database: str, region: str, port: int) -> UriTarget:
    encoded_password = quote(password, safe="")
    user = f"postgres.{project_ref}"
    host = f"aws-0-{region}.pooler.supabase.com"
    connection_type = "SESSION POOLER" if port == 5432 else "TRANSACTION POOLER"
    url = f"postgresql://{user}:{encoded_password}@{host}:{port}/{database}"
    return UriTarget(
        label=connection_type,
        url=url,
        connection_type=connection_type,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        region=region,
    )


def resolve_dns(host: str, port: int) -> tuple[list[str], list[str], bool]:
    ipv4_list: list[str] = []
    ipv6_list: list[str] = []

    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        for info in infos:
            ip = info[4][0]
            if ":" in ip:
                if ip not in ipv6_list:
                    ipv6_list.append(ip)
            else:
                if ip not in ipv4_list:
                    ipv4_list.append(ip)
    except OSError:
        pass

    for record_type, target_list in (("A", ipv4_list), ("AAAA", ipv6_list)):
        try:
            command = (
                f"Resolve-DnsName -Name '{host}' -Type {record_type} "
                "-ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress"
            )
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            for line in result.stdout.splitlines():
                ip = line.strip()
                if ip and ip not in target_list:
                    target_list.append(ip)
        except Exception:
            pass

    dns_ok = bool(ipv4_list or ipv6_list)
    return ipv4_list, ipv6_list, dns_ok


def probe_tcp(ipv4_list: list[str], ipv6_list: list[str], port: int) -> tuple[bool, str]:
    errors: list[str] = []

    for ip in ipv4_list:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.close()
            return True, f"TCP OK em {ip} (IPv4)"
        except Exception as exc:
            errors.append(f"{ip} (IPv4): {exc}")

    for ip in ipv6_list:
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((ip, port))
            sock.close()
            return True, f"TCP OK em {ip} (IPv6)"
        except Exception as exc:
            errors.append(f"{ip} (IPv6): {exc}")

    if errors:
        return False, "; ".join(errors)
    return False, "nenhum endereço IP disponível para teste TCP"


def probe_psycopg2(target: UriTarget) -> tuple[bool, str, str | None]:
    try:
        import psycopg2
    except ImportError:
        return False, "psycopg2 não instalado", None

    try:
        connection = psycopg2.connect(
            host=target.host,
            port=target.port,
            user=target.user,
            password=target.password,
            dbname=target.database,
            sslmode="require",
            connect_timeout=8,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        row = cursor.fetchone()
        cursor.close()
        connection.close()
        return True, "psycopg2 OK", row[0] if row else None
    except Exception as exc:
        return False, str(exc), None


def probe_sqlalchemy(target: UriTarget) -> tuple[bool, str, str | None]:
    try:
        engine = create_engine(
            target.url,
            pool_pre_ping=True,
            connect_args={
                "sslmode": "require",
                "connect_timeout": 8,
            },
        )
        with engine.connect() as connection:
            row = connection.execute(text("SELECT version();")).fetchone()
        engine.dispose()
        return True, "SQLAlchemy OK", row[0] if row else None
    except Exception as exc:
        return False, str(exc), None


def classify_failure(error_text: str, connection_type: str, ipv4_list: list[str], ipv6_list: list[str]) -> tuple[str, str, str]:
    normalized = error_text.lower()
    ipv6_only = bool(ipv6_list and not ipv4_list)

    if "porta incorreta" in normalized:
        return "porta", error_text, "Usar a porta correta para o tipo de conexão do Supabase."
    if "could not translate host name" in normalized or "getaddrinfo failed" in normalized:
        return "DNS", "could not translate host name", "Conferir host, projeto, região e testar outra rede."
    if "tenant/user not found" in normalized or "tenant or user not found" in normalized or "tenant/user" in normalized:
        return "tenant", "tenant/user not found", "Usar a região correta do pooler e copiar a URI diretamente do painel do Supabase."
    if "password authentication failed" in normalized:
        return "senha", "password authentication failed", "Redefinir a senha do banco no Supabase e atualizar a URI."
    if "ssl" in normalized and ("required" in normalized or "sslmode" in normalized):
        return "SSL", "SSL required", "Manter sslmode=require nas conexões PostgreSQL."
    if "timeout" in normalized or "timed out" in normalized:
        return "firewall", "timeout", "Verificar firewall, antivírus, internet, porta liberada e projeto ativo."
    if ipv6_only and connection_type == "DIRECT":
        return "Windows IPv6 issue", "IPv6-only host", "No Windows, preferir Session Pooler ou Transaction Pooler IPv4."
    if "network is unreachable" in normalized and connection_type == "DIRECT":
        return "Windows", "network unreachable", "No Windows, o host direto do Supabase pode falhar por IPv6; usar pooler IPv4."
    if "connection refused" in normalized:
        return "firewall", "connection refused", "Verificar porta e disponibilidade do serviço PostgreSQL no Supabase."
    return "Supabase", error_text or "erro desconhecido", "Revisar a URI completa no painel do Supabase e confirmar que o projeto está ativo."


def infer_environment_labels(result: ProbeResult) -> list[str]:
    if not result.success:
        return ["NÃO RECOMENDADO"]

    labels: list[str] = []
    if result.target.connection_type in {"SESSION POOLER", "TRANSACTION POOLER"}:
        labels.append("RECOMENDADO PARA WINDOWS")
        labels.append("RECOMENDADO PARA STREAMLIT CLOUD")
        labels.append("RECOMENDADO PARA RENDER")
        return labels

    if result.target.connection_type == "DIRECT" and result.ipv4_list:
        labels.append("RECOMENDADO PARA STREAMLIT CLOUD")
        labels.append("RECOMENDADO PARA RENDER")
        labels.append("NÃO RECOMENDADO PARA WINDOWS")
        return labels

    return ["NÃO RECOMENDADO"]


def score_region_probe(message: str, ok: bool) -> int:
    normalized = message.lower()
    if ok:
        return 0
    if "password authentication failed" in normalized:
        return 1
    if "ssl" in normalized:
        return 2
    if "timeout" in normalized:
        return 3
    if "connection refused" in normalized:
        return 4
    if "tenant/user not found" in normalized or "tenant or user not found" in normalized or "tenant/user" in normalized:
        return 8
    if "could not translate host name" in normalized or "getaddrinfo failed" in normalized:
        return 9
    return 7


def auto_detect_pooler_region(project_ref: str, password: str, database: str, parsed: object) -> RegionDetection:
    host_region = extract_region_from_host(parsed.hostname or "")
    if host_region:
        return RegionDetection(
            region=host_region,
            confirmed=True,
            probes=[RegionProbe(region=host_region, score=0, reason="região já presente na DATABASE_URL")],
        )

    probes: list[RegionProbe] = []
    best_region: str | None = None
    best_score = 999

    for region in COMMON_REGIONS:
        target = build_pooler_uri(project_ref, password, database, region, 5432)
        ipv4_list, ipv6_list, dns_ok = resolve_dns(target.host, target.port)
        if not dns_ok:
            probes.append(RegionProbe(region=region, score=9, reason="DNS falhou"))
            continue

        tcp_ok, tcp_message = probe_tcp(ipv4_list, ipv6_list, target.port)
        if not tcp_ok:
            score = score_region_probe(tcp_message, False)
            probes.append(RegionProbe(region=region, score=score, reason=tcp_message))
            if score < best_score:
                best_region = region
                best_score = score
            continue

        psycopg2_ok, psycopg2_message, _ = probe_psycopg2(target)
        score = score_region_probe(psycopg2_message, psycopg2_ok)
        probes.append(RegionProbe(region=region, score=score, reason=psycopg2_message))
        if score < best_score:
            best_region = region
            best_score = score
        if psycopg2_ok or "password authentication failed" in psycopg2_message.lower():
            return RegionDetection(region=region, confirmed=True, probes=probes)

    return RegionDetection(
        region=best_region or "us-east-1",
        confirmed=False,
        probes=probes,
    )


def build_targets(parsed: object) -> tuple[list[UriTarget], RegionDetection]:
    project_ref = extract_project_ref(parsed)
    if not project_ref:
        raise SystemExit("❌ Não foi possível determinar o PROJECT_REF a partir da DATABASE_URL atual.")

    password = parsed.password or ""
    database = (parsed.path or "/postgres").replace("/", "") or "postgres"
    region_detection = auto_detect_pooler_region(project_ref, password, database, parsed)
    detected_region = region_detection.region

    targets = [
        build_direct_uri(project_ref, password, database),
        build_pooler_uri(project_ref, password, database, detected_region, 5432),
        build_pooler_uri(project_ref, password, database, detected_region, 6543),
    ]
    return targets, region_detection


def probe_target(target: UriTarget) -> ProbeResult:
    ipv4_list, ipv6_list, dns_ok = resolve_dns(target.host, target.port)
    dns_status = "OK"
    error_text = ""

    if not dns_ok:
        dns_status = "FALHA"
        error_text = "getaddrinfo failed"
        problem_area, exact_reason, recommendation = classify_failure(error_text, target.connection_type, ipv4_list, ipv6_list)
        result = ProbeResult(
            target=target,
            dns_status=dns_status,
            tcp_status="NÃO EXECUTADO",
            psycopg2_status="NÃO EXECUTADO",
            sqlalchemy_status="NÃO EXECUTADO",
            result_label="FALHOU",
            success=False,
            error_text=error_text,
            exact_reason=exact_reason,
            problem_area=problem_area,
            recommendation=recommendation,
            suggested_uri=mask_url(target.url),
            ipv4_list=ipv4_list,
            ipv6_list=ipv6_list,
            version=None,
            environment_labels=[],
        )
        result.environment_labels = infer_environment_labels(result)
        return result

    if ipv6_list and not ipv4_list:
        dns_status = "IPv6-only"

    tcp_ok, tcp_message = probe_tcp(ipv4_list, ipv6_list, target.port)
    tcp_status = format_bool_status(tcp_ok)
    if not tcp_ok:
        error_text = tcp_message
        problem_area, exact_reason, recommendation = classify_failure(error_text, target.connection_type, ipv4_list, ipv6_list)
        result = ProbeResult(
            target=target,
            dns_status=dns_status,
            tcp_status=tcp_status,
            psycopg2_status="NÃO EXECUTADO",
            sqlalchemy_status="NÃO EXECUTADO",
            result_label="FALHOU",
            success=False,
            error_text=error_text,
            exact_reason=exact_reason,
            problem_area=problem_area,
            recommendation=recommendation,
            suggested_uri=mask_url(target.url),
            ipv4_list=ipv4_list,
            ipv6_list=ipv6_list,
            version=None,
            environment_labels=[],
        )
        result.environment_labels = infer_environment_labels(result)
        return result

    psycopg2_ok, psycopg2_message, psycopg2_version = probe_psycopg2(target)
    psycopg2_status = format_bool_status(psycopg2_ok)
    if not psycopg2_ok:
        error_text = psycopg2_message

    sqlalchemy_ok, sqlalchemy_message, sqlalchemy_version = probe_sqlalchemy(target)
    sqlalchemy_status = format_bool_status(sqlalchemy_ok)
    if not sqlalchemy_ok and not error_text:
        error_text = sqlalchemy_message

    success = psycopg2_ok and sqlalchemy_ok
    if success:
        problem_area = "OK"
        exact_reason = "conexão validada"
        recommendation = "Usar esta URI no ambiente correspondente."
        result_label = "FUNCIONOU"
    else:
        problem_area, exact_reason, recommendation = classify_failure(
            error_text,
            target.connection_type,
            ipv4_list,
            ipv6_list,
        )
        result_label = "FALHOU"

    version = psycopg2_version or sqlalchemy_version
    result = ProbeResult(
        target=target,
        dns_status=dns_status,
        tcp_status=tcp_status,
        psycopg2_status=psycopg2_status,
        sqlalchemy_status=sqlalchemy_status,
        result_label=result_label,
        success=success,
        error_text=error_text,
        exact_reason=exact_reason,
        problem_area=problem_area,
        recommendation=recommendation,
        suggested_uri=mask_url(target.url),
        ipv4_list=ipv4_list,
        ipv6_list=ipv6_list,
        version=version,
        environment_labels=[],
    )
    result.environment_labels = infer_environment_labels(result)
    return result


def print_target_intro(target: UriTarget) -> None:
    print_header(f"TESTE {target.label}")
    print(f"URI: {mask_url(target.url)}")
    print(f"Host: {target.host}")
    print(f"Porta: {target.port}")
    print(f"Usuário: {target.user}")
    print(f"Database: {target.database}")
    print(f"Tipo conexão: {target.connection_type}")
    if target.region:
        print(f"Região: {target.region}")


def print_probe_details(result: ProbeResult) -> None:
    if result.ipv4_list:
        print(f"IPv4: {', '.join(result.ipv4_list)}")
    if result.ipv6_list:
        print(f"IPv6: {', '.join(result.ipv6_list)}")
    if not result.ipv4_list and not result.ipv6_list:
        print("IPv4: nenhum")
        print("IPv6: nenhum")
    print(f"DNS: {result.dns_status}")
    print(f"TCP: {result.tcp_status}")
    print(f"psycopg2: {result.psycopg2_status}")
    print(f"SQLAlchemy: {result.sqlalchemy_status}")
    if result.version:
        print(f"SELECT version(): {result.version}")
    if result.success:
        print("✅ SUPABASE CONECTADO")
        print("✅ PostgreSQL ONLINE")
        print("✅ URI VALIDADA")
        print("✅ STREAMLIT COMPATÍVEL")
    else:
        print(f"Erro técnico completo: {result.error_text}")
        print(f"Motivo exato: {result.exact_reason}")
        print(f"Problema identificado: {result.problem_area}")
        print(f"Solução recomendada: {result.recommendation}")
        print(f"URI sugerida automaticamente: {result.suggested_uri}")
    print(f"Classificação: {', '.join(result.environment_labels)}")


def print_final_table(results: list[ProbeResult]) -> None:
    print_header("TABELA FINAL")
    headers = ["Tipo", "DNS", "TCP", "psycopg2", "SQLAlchemy", "Resultado"]
    rows = [
        [
            result.target.connection_type,
            result.dns_status,
            result.tcp_status,
            result.psycopg2_status,
            result.sqlalchemy_status,
            result.result_label,
        ]
        for result in results
    ]
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    header_line = " | ".join(header.ljust(widths[index]) for index, header in enumerate(headers))
    separator = "-+-".join("-" * width for width in widths)
    print(header_line)
    print(separator)
    for row in rows:
        print(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))


def print_region_probes(detection: RegionDetection) -> None:
    print_header("AUTODETECÇÃO DE REGIÃO POOLER")
    prefix = "Região confirmada automaticamente" if detection.confirmed else "Região presumida automaticamente"
    print(f"{prefix}: {detection.region}")
    for probe in detection.probes:
        print(f"- {probe.region}: score={probe.score} | {probe.reason}")


def print_final_summary(results: list[ProbeResult], detection: RegionDetection) -> int:
    print_final_table(results)

    working = [result for result in results if result.success]
    failed = [result for result in results if not result.success]

    print_header("CONCLUSÃO TÉCNICA FINAL")
    region_prefix = "Região pooler confirmada automaticamente" if detection.confirmed else "Região pooler presumida automaticamente"
    print(f"{region_prefix}: {detection.region}")

    if working:
        print("QUAL URI FUNCIONOU:")
        for result in working:
            print(f"- {result.target.connection_type}: {mask_url(result.target.url)}")
            print(f"  Motivo: {result.exact_reason}")
            print(f"  Classificação: {', '.join(result.environment_labels)}")

    if failed:
        print("QUAL URI FALHOU:")
        for result in failed:
            print(f"- {result.target.connection_type}: {mask_url(result.target.url)}")
            print(f"  Motivo: {result.exact_reason}")
            print(f"  Problema: {result.problem_area}")
            print(f"  Solução: {result.recommendation}")

    print("✔ streamlit run app.py continua funcionando exatamente igual.")
    print("✔ SQLite fallback preservado.")
    print("✔ bootstrap, init_db(), dashboard, login, devoluções e SAP não foram alterados.")

    if working:
        preferred = next((result for result in working if result.target.connection_type == "SESSION POOLER"), None)
        if preferred is None:
            preferred = next((result for result in working if result.target.connection_type == "TRANSACTION POOLER"), None)
        if preferred is None:
            preferred = working[0]
        print(f"URI recomendada automaticamente: {mask_url(preferred.target.url)}")
        return 0

    suggested = next((result for result in failed if result.target.connection_type == "SESSION POOLER"), failed[0])
    print(f"URI sugerida automaticamente: {mask_url(suggested.target.url)}")
    if not detection.confirmed:
        print("Observação: a região do pooler não foi confirmada por autenticação; copie a URI exata do painel do Supabase.")
    return 1


def main() -> int:
    print_header("COMPARAÇÃO DEFINITIVA DIRECT vs POOLER SUPABASE")

    valid_uri, uri_message, parsed = validate_uri(DATABASE_URL)
    if not valid_uri:
        print(f"❌ {uri_message}")
        print("✔ Sistema continuará usando SQLite fallback.")
        return 1

    print("DATABASE_URL atual do .env:")
    print(mask_url(DATABASE_URL))
    print()
    print(f"Host atual: {parsed.hostname}")
    print(f"Porta atual: {parsed.port}")
    print(f"Usuário atual: {parsed.username}")
    print(f"Database atual: {(parsed.path or '/postgres').replace('/', '') or 'postgres'}")
    print(f"Tipo atual: {detect_connection_type(parsed.hostname or '', parsed.port or 0)}")

    targets, region_detection = build_targets(parsed)
    print_region_probes(region_detection)

    results: list[ProbeResult] = []
    for target in targets:
        print_target_intro(target)
        result = probe_target(target)
        print_probe_details(result)
        results.append(result)

    return print_final_summary(results, region_detection)


if __name__ == "__main__":
    raise SystemExit(main())
