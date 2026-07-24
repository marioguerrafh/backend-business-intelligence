#!/usr/bin/env python3
"""Execute sync migration."""
import os
import sys

# Add app to path
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text

# Database URL from environment or default
db_url = os.getenv('DATABASE_URL', 'postgresql+psycopg://postgres:postgres@bi_postgres:5432/bi')

print("=" * 60)
print("EXECUTANDO MIGRATION DE SINCRONIZAÇÃO")
print("=" * 60)
print(f"\nDatabase: {db_url.replace('postgres:postgres', 'postgres:***')}\n")

# Read migration file
migration_path = '/app/migrations/2026-07-24-001-create-sync-tables.sql'
print(f"Lendo migration: {migration_path}")

with open(migration_path, 'r') as f:
    migration_sql = f.read()

# Split into statements
statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
print(f"Total de statements: {len(statements)}\n")

# Execute migration
engine = create_engine(db_url)
try:
    with engine.connect() as conn:
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            print(f"[{i}/{len(statements)}] Executando statement...")
            conn.execute(text(statement))
            conn.commit()
            print(f"    ✅ OK")
        
        # Verify tables created
        print("\n" + "=" * 60)
        print("VERIFICANDO TABELAS CRIADAS")
        print("=" * 60)
        
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_name LIKE 'sync_%' ORDER BY table_name"
        ))
        tables = [row[0] for row in result]
        
        if tables:
            print(f"\n✅ {len(tables)} tabelas criadas:")
            for table in tables:
                print(f"   - {table}")
        else:
            print("\n⚠️  Nenhuma tabela sync_* encontrada!")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION EXECUTADA COM SUCESSO!")
        print("=" * 60)
        
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
