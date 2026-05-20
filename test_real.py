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

print()
print("DATABASE_URL REAL:")
print(DATABASE_URL)
print()

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "sslmode": "require"
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
