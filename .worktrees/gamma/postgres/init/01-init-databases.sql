-- Create databases for Langflow and n8n
CREATE DATABASE langflow;
CREATE DATABASE n8n;

-- Create users
CREATE USER langflow WITH PASSWORD 'langflow';
CREATE USER n8n WITH PASSWORD 'n8n';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE langflow TO langflow;
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n;

-- Connect to langflow database and grant schema privileges
\c langflow;
GRANT ALL ON SCHEMA public TO langflow;

-- Connect to n8n database and grant schema privileges
\c n8n;
GRANT ALL ON SCHEMA public TO n8n;
