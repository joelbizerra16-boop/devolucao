"""Audita todos os arquivos devolucao.db encontrados no ambiente."""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEARCH_ROOTS = [
    ROOT,
    ROOT.parent / "FINALIZADO",
]

CANDIDATES: list[Path] = []
for base in SEARCH_ROOTS:
    if base.exists():
        CANDIDATES.extend(base.rglob("devolucao.db"))

CANDIDATES = sorted(set(CANDIDATES), key=lambda p: p.stat().st_mtime, reverse=True)


def audit_db(path: Path) -> dict:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    counts = {}
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM [{t}]")
        counts[t] = cur.fetchone()[0]
    extras = {}
    if "usuarios" in tables:
        cur.execute("SELECT COUNT(*), MAX(id) FROM usuarios")
        extras["usuarios"] = cur.fetchone()
        cur.execute("SELECT id, username, nome FROM usuarios ORDER BY id")
        extras["usuarios_list"] = cur.fetchall()
    for t in ("devolucoes", "devolucoes_legado"):
        if t in tables:
            cur.execute(f"SELECT COUNT(*), MIN(id), MAX(id) FROM [{t}]")
            extras[t] = cur.fetchone()
    conn.close()
    st = path.stat()
    return {
        "path": str(path),
        "size": st.st_size,
        "modified": datetime.fromtimestamp(st.st_mtime).isoformat(),
        "counts": counts,
        "extras": extras,
    }


def main() -> None:
    print("AUDITORIA DE TODAS AS FONTES SQLite\n")
    best = None
    for p in CANDIDATES:
        a = audit_db(p)
        u = a["counts"].get("usuarios", 0)
        d = a["counts"].get("devolucoes", 0)
        dl = a["counts"].get("devolucoes_legado", 0)
        print(f"\n{p}")
        print(f"  mod={a['modified']} size={a['size']:,}")
        print(f"  usuarios={u} devolucoes={d} legado={dl} motivos={a['counts'].get('motivos',0)} sap={a['counts'].get('dados_sap',0)}")
        if a.get("extras", {}).get("usuarios_list"):
            for row in a["extras"]["usuarios_list"]:
                print(f"    user: {row}")
        score = u * 10 + d + dl
        if best is None or score > best[0]:
            best = (score, a)
    if best:
        print("\n>>> MELHOR CANDIDATO (mais usuarios+devolucoes):")
        print(f"    {best[1]['path']}")


if __name__ == "__main__":
    main()
