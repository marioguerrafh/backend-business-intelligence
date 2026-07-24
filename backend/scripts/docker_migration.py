"""Executar migration dentro do container Docker."""
from sqlalchemy import create_engine, text

print("🔄 Executando migration...")

# Conectar ao banco (dentro do Docker)
engine = create_engine('postgresql+psycopg://postgres:postgres@bi_postgres:5432/bi')

# Ler migration
with open('/app/migrations/2026-07-24-001-create-sync-tables.sql', 'r') as f:
    sql = f.read()

# Executar
with engine.connect() as conn:
    for statement in sql.split(';'):
        if statement.strip():
            conn.execute(text(statement))
    conn.commit()
    
    # Verificar
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name LIKE 'sync_%'
        ORDER BY table_name
    """))
    
    tables = [r[0] for r in result.fetchall()]
    print(f"\n✅ Migration executada!")
    print(f"Tabelas criadas: {tables}")
