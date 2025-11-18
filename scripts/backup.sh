#!/bin/bash
# Complete backup script for OsMEN
# Creates timestamped backups of all critical components

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="osmen_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

echo "🔄 Starting OsMEN Backup"
echo "======================================"
echo "Backup location: ${BACKUP_PATH}"
echo ""

# Create backup directory
mkdir -p "${BACKUP_PATH}"

# 1. Backup PostgreSQL
echo "📦 Backing up PostgreSQL..."
if docker ps | grep -q osmen-postgres; then
    docker exec osmen-postgres pg_dumpall -U postgres > "${BACKUP_PATH}/postgres_backup.sql"
    echo "  ✅ PostgreSQL backed up"
else
    echo "  ⚠️  PostgreSQL container not running"
fi

# 2. Backup Qdrant (if running)
echo "📦 Backing up Qdrant vectors..."
if docker ps | grep -q qdrant; then
    docker cp osmen-qdrant:/qdrant/storage "${BACKUP_PATH}/qdrant_data" 2>/dev/null || echo "  ⚠️  Could not backup Qdrant"
    echo "  ✅ Qdrant backed up"
else
    echo "  ⚠️  Qdrant container not running"
fi

# 3. Backup configuration
echo "📦 Backing up configuration..."
if [ -f .env ]; then
    cp .env "${BACKUP_PATH}/env_backup"
    echo "  ✅ .env backed up"
else
    echo "  ⚠️  No .env file found"
fi

if [ -d config ]; then
    cp -r config "${BACKUP_PATH}/"
    echo "  ✅ config/ backed up"
fi

# 4. Backup n8n workflows
echo "📦 Backing up n8n workflows..."
if docker ps | grep -q n8n; then
    docker cp osmen-n8n:/home/node/.n8n "${BACKUP_PATH}/n8n_data" 2>/dev/null || echo "  ⚠️  Could not backup n8n"
    echo "  ✅ n8n backed up"
else
    echo "  ⚠️  n8n container not running"
fi

# 5. Backup Langflow flows
echo "📦 Backing up Langflow flows..."
if [ -d langflow/flows ]; then
    cp -r langflow/flows "${BACKUP_PATH}/"
    echo "  ✅ Langflow flows backed up"
fi

# 6. Backup user content
echo "📦 Backing up user content..."
if [ -d content ]; then
    cp -r content "${BACKUP_PATH}/"
    echo "  ✅ content/ backed up"
fi

if [ -d obsidian-vault ]; then
    cp -r obsidian-vault "${BACKUP_PATH}/"
    echo "  ✅ obsidian-vault/ backed up"
fi

# 7. Create manifest
echo "📦 Creating backup manifest..."
cat > "${BACKUP_PATH}/manifest.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "$(cat VERSION 2>/dev/null || echo 'unknown')",
  "hostname": "$(hostname)",
  "components": [
    "postgres",
    "qdrant",
    "config",
    "n8n",
    "langflow",
    "content"
  ]
}
EOF
echo "  ✅ Manifest created"

# 8. Compress backup
echo "📦 Compressing backup..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${BACKUP_DIR}" "${BACKUP_NAME}"
rm -rf "${BACKUP_PATH}"

echo ""
echo "======================================"
echo "✅ Backup complete!"
echo ""
echo "Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "Size: $(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)"
echo ""
echo "To restore this backup:"
echo "  ./scripts/restore.sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo ""
echo "To validate this backup:"
echo "  python3 scripts/automation/validate_backup.py ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
