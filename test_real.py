from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

print("===================================")
print("TESTE REAL SUPABASE")
print("===================================")

dotenv_ok = load_dotenv(".env")

print()
print(f".env carregado: {dotenv_ok}")

DATABASE_URL = os.getenv("DATABASE_URL")

from core.environment import resolve_sslmode
from core.redaction import redact_secrets
from database.connection import sqlalchemy_url

print()
print("DATABASE_URL (mascarada):")
print(redact_secrets(DATABASE_URL or ""))
print()

engine = create_engine(
    sqlalchemy_url(DATABASE_URL),
    pool_pre_ping=True,
    connect_args={
        "sslmode": resolve_sslmode(),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
    }
)

try:

    with engine.connect() as conn:

        result = conn.execute(
            text("SELECT version();")
        )

        print()
        print("✅ SUPABASE CONECTADO")
        print("✅ PostgreSQL ONLINE")
        print("✅ URI VALIDADA")
        print()

        for row in result:
            print(row[0])

except Exception as e:

    print()
    print("❌ ERRO REAL")
    print(type(e).__name__)
    print(e)
