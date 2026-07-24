-- Migration: Create sync_checkpoints and sync_jobs tables
-- Version: 2026-07-24-001
-- Description: Tables for synchronization orchestration with checkpoint-based recovery

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
    mode VARCHAR(20) NOT NULL DEFAULT 'incremental',
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

CREATE INDEX IF NOT EXISTS idx_sync_jobs_company_provider 
ON sync_jobs(company_id, provider);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_status 
ON sync_jobs(status);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_priority_created 
ON sync_jobs(priority, created_at);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_domain 
ON sync_jobs(domain);

CREATE INDEX IF NOT EXISTS idx_sync_jobs_checkpoint 
ON sync_jobs(checkpoint_id);

-- Add comment
COMMENT ON TABLE sync_checkpoints IS 'Stores synchronization checkpoints for resumable sync operations';
COMMENT ON TABLE sync_jobs IS 'Stores synchronization jobs for orchestrated domain-based syncs';
