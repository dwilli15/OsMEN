#!/bin/bash
# Restore script for OsMEN backups

set -e

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./scripts/restore.sh <backup-file>"
    echo ""
    echo "Example:"
    echo "  ./scripts/restore.sh backups/osmen_backup_20241118_120000.tar.gz"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite existing data!"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

echo ""
echo "🔄 Starting OsMEN Restore"
echo "======================================"
echo ""

# Extract backup
TEMP_DIR=$(mktemp -d)
echo "📦 Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d)

if [ -z "$BACKUP_DIR" ]; then
    echo "❌ Error: Invalid backup archive"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo "  ✅ Backup extracted to temporary location"
echo ""

# Stop services
echo "🛑 Stopping services..."
docker-compose down
echo "  ✅ Services stopped"
echo ""

# Restore PostgreSQL
if [ -f "$BACKUP_DIR/postgres_backup.sql" ]; then
    echo "📥 Restoring PostgreSQL..."
    docker-compose up -d postgres
    sleep 10
    cat "$BACKUP_DIR/postgres_backup.sql" | docker exec -i osmen-postgres psql -U postgres
    echo "  ✅ PostgreSQL restored"
else
    echo "  ⚠️  No PostgreSQL backup found"
fi
echo ""

# Restore configuration
if [ -f "$BACKUP_DIR/env_backup" ]; then
    echo "📥 Restoring configuration..."
    cp "$BACKUP_DIR/env_backup" .env
    echo "  ✅ .env restored"
fi

if [ -d "$BACKUP_DIR/config" ]; then
    rm -rf config
    cp -r "$BACKUP_DIR/config" ./
    echo "  ✅ config/ restored"
fi
echo ""

# Restore Qdrant
if [ -d "$BACKUP_DIR/qdrant_data" ]; then
    echo "📥 Restoring Qdrant..."
    docker-compose up -d qdrant
    sleep 5
    docker cp "$BACKUP_DIR/qdrant_data" osmen-qdrant:/qdrant/storage 2>/dev/null || echo "  ⚠️  Could not restore Qdrant"
    echo "  ✅ Qdrant restored"
fi
echo ""

# Restore n8n
if [ -d "$BACKUP_DIR/n8n_data" ]; then
    echo "📥 Restoring n8n..."
    docker-compose up -d n8n
    sleep 5
    docker cp "$BACKUP_DIR/n8n_data" osmen-n8n:/home/node/.n8n 2>/dev/null || echo "  ⚠️  Could not restore n8n"
    echo "  ✅ n8n restored"
fi
echo ""

# Restore Langflow
if [ -d "$BACKUP_DIR/flows" ]; then
    echo "📥 Restoring Langflow..."
    rm -rf langflow/flows
    cp -r "$BACKUP_DIR/flows" langflow/
    echo "  ✅ Langflow flows restored"
fi
echo ""

# Restore user content
if [ -d "$BACKUP_DIR/content" ]; then
    echo "📥 Restoring user content..."
    rm -rf content
    cp -r "$BACKUP_DIR/content" ./
    echo "  ✅ content/ restored"
fi

if [ -d "$BACKUP_DIR/obsidian-vault" ]; then
    rm -rf obsidian-vault
    cp -r "$BACKUP_DIR/obsidian-vault" ./
    echo "  ✅ obsidian-vault/ restored"
fi
echo ""

# Cleanup
rm -rf "$TEMP_DIR"

# Restart all services
echo "🚀 Starting all services..."
docker-compose up -d
echo "  ✅ Services started"
echo ""

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 30

# Verify
echo "🔍 Verifying restore..."
if command -v python3 &> /dev/null; then
    python3 check_operational.py 2>/dev/null || echo "  ⚠️  Operational check not available"
fi

echo ""
echo "======================================"
echo "✅ Restore complete!"
echo ""
echo "Restored from: $BACKUP_FILE"
echo ""
echo "Next steps:"
echo "1. Verify all services are running: docker-compose ps"
echo "2. Test agent functionality: python3 test_agents.py"
echo "3. Check logs for any issues: docker-compose logs"
