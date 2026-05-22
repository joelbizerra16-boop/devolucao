"""Atalho: delega para migrate_sqlite_to_supabase.py na raiz."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from migrate_sqlite_to_supabase import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
