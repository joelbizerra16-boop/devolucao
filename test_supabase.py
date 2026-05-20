"""Teste e diagnóstico de conexão Supabase PostgreSQL."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).resolve().parent / ".env")

from database.connection import DATABASE_URL, is_postgres  # noqa: E402


def _diagnostico_dns(host: str) -> None:
    print(f"\n--- DNS: {host} ---")
    try:
        infos = socket.getaddrinfo(host, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for family, *_rest, sockaddr in infos[:4]:
            fam = "IPv6" if family == socket.AF_INET6 else "IPv4"
            print(f"  {fam}: {sockaddr[0]}")
    except OSError as exc:
        print(f"  Python não resolveu: {exc}")
        print(
            "  No Windows, hosts db.*.supabase.co costumam ser só IPv6.\n"
            "  Use a URI do **Session pooler** no painel Supabase (porta 5432 ou 6543)."
        )


if not is_postgres():
    print("ERRO: DATABASE_URL não aponta para PostgreSQL.")
    print("Defina DATABASE_URL no arquivo .env (copie do painel Supabase → Connect).")
    raise SystemExit(1)

parsed = urlparse(DATABASE_URL)
host = parsed.hostname or ""
user = parsed.username or ""
port = parsed.port or 5432

print("DATABASE_URL (host):", host)
print("Usuário:", user)
print("Porta:", port)

if host.startswith("db.") and port == 6543:
    print("\nAVISO: Porta 6543 no host db.* está incorreta. Use 5432 (direto) ou o host pooler.")

if "pooler.supabase.com" in host and user == "postgres":
    ref = os.getenv("SUPABASE_PROJECT_REF", "SEU_PROJECT_REF")
    print(
        f"\nAVISO: No pooler o usuário deve ser postgres.{ref}\n"
        f"Exemplo: postgresql://postgres.{ref}:SENHA@{host}:{port}/postgres"
    )

if host and not host.startswith("["):
    _diagnostico_dns(host.replace("[", "").replace("]", ""))

print("\n--- Teste de conexão ---")
try:
    eng = create_engine(
        DATABASE_URL,
        connect_args={"sslmode": "require", "connect_timeout": 10},
    )
    with eng.connect() as conn:
        row = conn.execute(text("SELECT version();")).fetchone()
    print("SUPABASE CONECTADO")
    if row:
        print(row[0])
except Exception as exc:
    print("ERRO:")
    print(exc)
    msg = str(exc).lower()
    if "could not translate host name" in msg:
        print(
            "\nDica: copie a URI **Session pooler** em "
            "Supabase → Project Settings → Database → Connect."
        )
    elif "tenant" in msg or "not found" in msg:
        print(
            "\nDica: projeto pausado, região errada ou PROJECT_REF incorreto.\n"
            "Confira no painel se o projeto está ativo e cole a URI completa."
        )
    elif "network is unreachable" in msg:
        print(
            "\nDica: sua rede não tem IPv6. Use obrigatoriamente o **pooler** (IPv4), "
            "não o host db.*.supabase.co direto."
        )
    raise SystemExit(1) from exc
