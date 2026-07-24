"""
Script para executar migration de sincronização.
"""
import os
import sys
from pathlib import Path

print("=" * 60)
print("SCRIPT DE MIGRATION - INICIADO")
print("=" * 60)

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

print(f"Backend path: {backend_path}")

try:
    from sqlalchemy import create_engine, text
    from app.config.settings import settings
    print("✓ Imports realizados com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar módulos: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def run_migration():
    """Executar migration SQL."""
    print("🔄 Executando migration de sincronização...")
    
    # Ler arquivo SQL
    migration_file = backend_path / "migrations" / "2026-07-24-001-create-sync-tables.sql"
    
    if not migration_file.exists():
        print(f"❌ Arquivo de migration não encontrado: {migration_file}")
        return False
    
    print(f"📄 Arquivo de migration encontrado: {migration_file}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"📊 SQL content size: {len(sql_content)} bytes")
    
    # Executar migration
    try:
        # Obter database URL
        db_url = str(settings.database_url)
        print(f"🔌 Conectando ao banco: {db_url.replace('postgres:postgres', 'postgres:***')}")
        
        engine = create_engine(db_url)
        
        # Testar conexão
        print("🔍 Testando conexão...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Conexão estabelecida com sucesso!")
            
            # Executar SQL
            print("\n📝 Executando statements SQL...")
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            
            print(f"Total de statements: {len(statements)}")
            
            for i, statement in enumerate(statements, 1):
                if statement:
                    # Mostrar primeiros 50 caracteres do statement
                    preview = statement[:50].replace('\n', ' ')
                    print(f"  [{i}/{len(statements)}] {preview}...")
                    conn.execute(text(statement))
            
            conn.commit()
            print("✓ Commit realizado!")
        
        print("\n✅ Migration executada com sucesso!")
        print("\nTabelas criadas:")
        print("  - sync_checkpoints")
        print("  - sync_jobs")
        print("\nÍndices criados:")
        print("  - idx_sync_checkpoints_company_provider_domain")
        print("  - idx_sync_checkpoints_status")
        print("  - idx_sync_checkpoints_updated")
        print("  - idx_sync_jobs_company_provider_domain")
        print("  - idx_sync_jobs_status")
        print("  - idx_sync_jobs_priority_created")
        print("  - idx_sync_jobs_updated")
        
        # Verificar tabelas
        print("\n🔍 Verificando tabelas...")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'sync_%'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                print(f"✓ Encontradas {len(tables)} tabelas:")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠️  Nenhuma tabela sync_* encontrada")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao executar migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("INICIANDO EXECUÇÃO")
    print("=" * 60 + "\n")
    
    try:
        success = run_migration()
        print(f"\nResultado: {'SUCESSO' if success else 'FALHA'}")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
