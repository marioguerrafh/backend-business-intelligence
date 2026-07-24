import psycopg

conn = psycopg.connect("host=localhost port=5432 dbname=bi user=postgres password=postgres")
cur = conn.cursor()

sql = open(r"d:\Projetos\business-intelligence\backend\migrations\2026-07-24-001-create-sync-tables.sql").read()

for statement in sql.split(';'):
    if statement.strip():
        cur.execute(statement)

conn.commit()

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'sync_%'")
print("Tabelas criadas:", [r[0] for r in cur.fetchall()])

cur.close()
conn.close()
print("\n✅ Migration executada com sucesso!")
