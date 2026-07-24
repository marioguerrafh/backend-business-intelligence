"""Script simples para executar migration."""
import psycopg

# Configuração do banco
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "bi",
    "user": "postgres",
    "password": "postgres"
}

# SQL da migration
SQL = """
-- Create sync_checkpoints table
CREATE TABLE IF NOT EXISTS sync_checkpoints (
    checkpoint_id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_page INTEGER,
    last_cursor TEXT,
    last_success_sync TIMESTAMP,
    last_processed_record TEXT,
    last_window_start DATE,
    last_window_end DATE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sync_checkpoints_company_provider_domain 
ON sync_checkpoints(company_id, provider, domain);

CREATE INDEX IF NOT EXISTS idx_sync_checkpoints_status 
ON sync_checkpoints(status);

CREATE INDEX IF NOT EXISTS idx_sync_checkpoints_updated 
ON sync_checkpoints(updated_at DESC);

-- Create sync_jobs table
CREATE TABLE IF NOT EXISTS sync_jobs (
    job_id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal',
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    mode VARCHAR(20) NOT NULL DEFAULT 'full',
    checkpoint_id VARCHAR(36),
    window_start DATE,
    window_end DATE,
    window_id VARCHAR(36),
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    records_read INTEGER DEFAULT 0,
    records_imported INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    pages_processed INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (checkpoint_id) REFERENCES sync_checkpoints(checkpoint_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_company_provider_domain 
ON sync_jobs(company_id, provider, domain);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_status 
ON sync_jobs(status);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_priority_created 
ON sync_jobs(priority, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_updated 
ON sync_jobs(updated_at DESC);
"""

print("🔄 Executando migration...")

try:
    # Conectar ao banco
    print(f"Conectando em {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}...")
    
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            # Executar SQL
            print("Executando SQL...")
            cur.execute(SQL)
            conn.commit()
    
    print("\n✅ Migration executada com sucesso!")
    print("\nTabelas criadas:")
    print("  - sync_checkpoints")
    print("  - sync_jobs")
    
    # Verificar tabelas
    print("\n🔍 Verificando tabelas criadas...")
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'sync_%'
                ORDER BY table_name
            """)
            
            tables = cur.fetchall()
            if tables:
                print(f"✓ Encontradas {len(tables)} tabelas:")
                for (table,) in tables:
                    print(f"  - {table}")
            else:
                print("⚠️  Nenhuma tabela sync_* encontrada")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
