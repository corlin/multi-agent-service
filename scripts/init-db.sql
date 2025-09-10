-- Patent MVP System Database Initialization Script
-- This script sets up the initial database schema and data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS patent_data;
CREATE SCHEMA IF NOT EXISTS agent_state;
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Patent data tables
CREATE TABLE IF NOT EXISTS patent_data.patents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_number VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    applicants TEXT[],
    inventors TEXT[],
    application_date DATE,
    publication_date DATE,
    ipc_classes TEXT[],
    country VARCHAR(10),
    status VARCHAR(50),
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patent_data.patent_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(100) UNIQUE NOT NULL,
    keywords TEXT[],
    patent_count INTEGER,
    analysis_result JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS patent_data.patent_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID REFERENCES patent_data.patent_analyses(id),
    report_type VARCHAR(50),
    file_path TEXT,
    file_size BIGINT,
    mime_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent state tables
CREATE TABLE IF NOT EXISTS agent_state.workflow_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    workflow_type VARCHAR(50),
    current_state VARCHAR(50),
    state_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_state.agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id VARCHAR(100),
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    request_data JSONB,
    response_data JSONB,
    status VARCHAR(50),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    error_message TEXT
);

-- Monitoring tables
CREATE TABLE IF NOT EXISTS monitoring.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100),
    metric_value NUMERIC,
    metric_unit VARCHAR(20),
    tags JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS monitoring.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100),
    check_name VARCHAR(100),
    status VARCHAR(20),
    response_time_ms INTEGER,
    error_message TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_patents_application_number ON patent_data.patents(application_number);
CREATE INDEX IF NOT EXISTS idx_patents_application_date ON patent_data.patents(application_date);
CREATE INDEX IF NOT EXISTS idx_patents_country ON patent_data.patents(country);
CREATE INDEX IF NOT EXISTS idx_patents_ipc_classes ON patent_data.patents USING GIN(ipc_classes);
CREATE INDEX IF NOT EXISTS idx_patents_applicants ON patent_data.patents USING GIN(applicants);
CREATE INDEX IF NOT EXISTS idx_patents_title_search ON patent_data.patents USING GIN(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_patents_abstract_search ON patent_data.patents USING GIN(to_tsvector('english', abstract));

CREATE INDEX IF NOT EXISTS idx_analyses_status ON patent_data.patent_analyses(status);
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON patent_data.patent_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_analyses_keywords ON patent_data.patent_analyses USING GIN(keywords);

CREATE INDEX IF NOT EXISTS idx_workflow_states_type ON agent_state.workflow_states(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflow_states_updated ON agent_state.workflow_states(updated_at);

CREATE INDEX IF NOT EXISTS idx_agent_executions_agent ON agent_state.agent_executions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_status ON agent_state.agent_executions(status);
CREATE INDEX IF NOT EXISTS idx_agent_executions_started ON agent_state.agent_executions(started_at);

CREATE INDEX IF NOT EXISTS idx_metrics_name_timestamp ON monitoring.system_metrics(metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_health_checks_service_timestamp ON monitoring.health_checks(service_name, timestamp);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patents_updated_at BEFORE UPDATE ON patent_data.patents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_states_updated_at BEFORE UPDATE ON agent_state.workflow_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data
INSERT INTO monitoring.system_metrics (metric_name, metric_value, metric_unit, tags)
VALUES 
    ('system.initialized', 1, 'boolean', '{"component": "database", "version": "1.0"}'),
    ('database.schema_version', 1, 'version', '{"schema": "patent_mvp"}')
ON CONFLICT DO NOTHING;

-- Create views for common queries
CREATE OR REPLACE VIEW patent_data.patent_summary AS
SELECT 
    COUNT(*) as total_patents,
    COUNT(DISTINCT country) as countries_count,
    COUNT(DISTINCT unnest(applicants)) as unique_applicants,
    MIN(application_date) as earliest_date,
    MAX(application_date) as latest_date
FROM patent_data.patents;

CREATE OR REPLACE VIEW monitoring.recent_health_status AS
SELECT DISTINCT ON (service_name, check_name)
    service_name,
    check_name,
    status,
    response_time_ms,
    timestamp
FROM monitoring.health_checks
ORDER BY service_name, check_name, timestamp DESC;

-- Grant permissions
GRANT USAGE ON SCHEMA patent_data TO patent_user;
GRANT USAGE ON SCHEMA agent_state TO patent_user;
GRANT USAGE ON SCHEMA monitoring TO patent_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA patent_data TO patent_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent_state TO patent_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO patent_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA patent_data TO patent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent_state TO patent_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO patent_user;

-- Create development user (for development environment)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'dev_user') THEN
        CREATE ROLE dev_user LOGIN PASSWORD 'dev_pass';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA patent_data TO dev_user;
GRANT USAGE ON SCHEMA agent_state TO dev_user;
GRANT USAGE ON SCHEMA monitoring TO dev_user;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA patent_data TO dev_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA agent_state TO dev_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA monitoring TO dev_user;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA patent_data TO dev_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA agent_state TO dev_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA monitoring TO dev_user;