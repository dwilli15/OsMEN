#!/bin/bash
# OsMEN v3.0 - Automated Backup Script
# Backs up PostgreSQL, Qdrant, and critical configuration files

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/osmen}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
S3_BUCKET="${S3_BUCKET:-}"  # Optional: s3://your-bucket/osmen-backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Database credentials
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-osmen}"
POSTGRES_DB="${POSTGRES_DB:-osmen}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting OsMEN backup - $TIMESTAMP"

# Backup PostgreSQL
log "Backing up PostgreSQL databases..."
PG_BACKUP_FILE="$BACKUP_DIR/postgres_${TIMESTAMP}.sql.gz"

if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean --if-exists --create | gzip > "$PG_BACKUP_FILE"; then
    log "✅ PostgreSQL backup created: $(basename $PG_BACKUP_FILE) ($(du -h $PG_BACKUP_FILE | cut -f1))"
else
    error "PostgreSQL backup failed"
    exit 1
fi

# Backup Langflow database
if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "langflow" \
    --clean --if-exists --create | gzip > "$BACKUP_DIR/langflow_${TIMESTAMP}.sql.gz" 2>/dev/null; then
    log "✅ Langflow database backed up"
fi

# Backup n8n database
if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "n8n" \
    --clean --if-exists --create | gzip > "$BACKUP_DIR/n8n_${TIMESTAMP}.sql.gz" 2>/dev/null; then
    log "✅ n8n database backed up"
fi

# Backup Qdrant collections
log "Backing up Qdrant vector database..."
QDRANT_BACKUP_DIR="$BACKUP_DIR/qdrant_${TIMESTAMP}"
mkdir -p "$QDRANT_BACKUP_DIR"

# Get list of collections
if curl -s "http://${QDRANT_HOST}:${QDRANT_PORT}/collections" -o "$QDRANT_BACKUP_DIR/collections.json"; then
    # Create snapshots for each collection
    COLLECTIONS=$(cat "$QDRANT_BACKUP_DIR/collections.json" | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")
    
    if [ -n "$COLLECTIONS" ]; then
        for collection in $COLLECTIONS; do
            log "Creating snapshot for collection: $collection"
            if curl -X POST "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/$collection/snapshots" \
                -H "Content-Type: application/json" -o "$QDRANT_BACKUP_DIR/${collection}_snapshot.json"; then
                log "✅ Snapshot created for $collection"
            fi
        done
    else
        warn "No Qdrant collections found or Qdrant not accessible"
    fi
    
    # Compress Qdrant backup
    tar -czf "$BACKUP_DIR/qdrant_${TIMESTAMP}.tar.gz" -C "$BACKUP_DIR" "qdrant_${TIMESTAMP}"
    rm -rf "$QDRANT_BACKUP_DIR"
    log "✅ Qdrant backup compressed"
else
    warn "Could not connect to Qdrant at ${QDRANT_HOST}:${QDRANT_PORT}"
fi

# Backup configuration files
log "Backing up configuration files..."
CONFIG_BACKUP_FILE="$BACKUP_DIR/config_${TIMESTAMP}.tar.gz"

tar -czf "$CONFIG_BACKUP_FILE" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='*.log' \
    --exclude='.git' \
    -C / \
    $([ -f /.env ] && echo ".env") \
    $([ -d /.copilot ] && echo ".copilot") \
    $([ -d /langflow/config ] && echo "langflow/config") \
    $([ -d /n8n/workflows ] && echo "n8n/workflows") \
    2>/dev/null || true

if [ -f "$CONFIG_BACKUP_FILE" ]; then
    log "✅ Configuration backup created: $(basename $CONFIG_BACKUP_FILE) ($(du -h $CONFIG_BACKUP_FILE | cut -f1))"
fi

# Backup encrypted tokens
if [ -d "/.copilot/tokens" ]; then
    TOKENS_BACKUP="$BACKUP_DIR/tokens_${TIMESTAMP}.tar.gz.enc"
    tar -czf - /.copilot/tokens | openssl enc -aes-256-cbc -salt -pbkdf2 -pass pass:"${BACKUP_ENCRYPTION_KEY:-osmen-backup}" > "$TOKENS_BACKUP"
    log "✅ Encrypted tokens backup created"
fi

# Create manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${TIMESTAMP}.txt" << EOF
OsMEN Backup Manifest
=====================
Timestamp: $TIMESTAMP
Date: $(date)
Host: $(hostname)

PostgreSQL Backups:
- Main DB: $(basename $PG_BACKUP_FILE) ($(du -h $PG_BACKUP_FILE 2>/dev/null | cut -f1 || echo "N/A"))
- Langflow: langflow_${TIMESTAMP}.sql.gz
- n8n: n8n_${TIMESTAMP}.sql.gz

Qdrant Backup:
- Collections: qdrant_${TIMESTAMP}.tar.gz

Configuration:
- Files: config_${TIMESTAMP}.tar.gz
- Tokens: tokens_${TIMESTAMP}.tar.gz.enc (encrypted)

Total Backup Size: $(du -sh $BACKUP_DIR | cut -f1)
EOF

log "✅ Manifest created"

# Upload to S3 if configured
if [ -n "$S3_BUCKET" ]; then
    log "Uploading backups to S3: $S3_BUCKET"
    
    if command -v aws &> /dev/null; then
        aws s3 sync "$BACKUP_DIR" "$S3_BUCKET/$(date +%Y/%m/%d)/" \
            --exclude "*" \
            --include "*${TIMESTAMP}*" \
            --storage-class STANDARD_IA
        
        log "✅ Backups uploaded to S3"
    else
        warn "AWS CLI not found, skipping S3 upload"
    fi
fi

# Clean up old backups
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz.enc" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "manifest_*.txt" -type f -mtime +$RETENTION_DAYS -delete

log "✅ Old backups cleaned up"

# Summary
echo ""
log "========================================="
log "Backup completed successfully!"
log "========================================="
log "Backup location: $BACKUP_DIR"
log "Timestamp: $TIMESTAMP"
log "Total size: $(du -sh $BACKUP_DIR | cut -f1)"
log "Retention: $RETENTION_DAYS days"
echo ""

# Exit successfully
exit 0
