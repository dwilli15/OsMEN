# Backup and Recovery Guide

Comprehensive guide for backing up and recovering OsMEN data in production environments.

## Overview

OsMEN stores data across multiple services. A complete backup strategy must include:

1. **PostgreSQL Database** - Persistent data
2. **Qdrant Vectors** - Agent memory
3. **Configuration Files** - Settings and secrets
4. **n8n Workflows** - Automation definitions
5. **Langflow Flows** - Agent flows
6. **User Data** - Obsidian vaults, uploaded content

## What to Backup

### Critical (Must Backup)

| Component | Location | Frequency | Priority |
|-----------|----------|-----------|----------|
| PostgreSQL DB | Docker volume `postgres_data` | Hourly | Critical |
| Configuration | `.env`, `config/` | On change | Critical |
| Qdrant Vectors | Docker volume `qdrant_data` | Daily | High |
| n8n Workflows | Docker volume `n8n_data` | Daily | High |
| Langflow Flows | `langflow/flows/` | Daily | High |

### Important (Should Backup)

| Component | Location | Frequency | Priority |
|-----------|----------|-----------|----------|
| Obsidian Vault | `OBSIDIAN_VAULT_PATH` | Daily | Medium |
| User Content | `content/` | Daily | Medium |
| Logs | `logs/` | Weekly | Low |
| Cache | Redis (optional) | Never | N/A |

### Optional

| Component | Location | Notes |
|-----------|----------|-------|
| Docker Images | Local cache | Can be rebuilt |
| Dependencies | `node_modules`, Python packages | Can be reinstalled |
| Temporary Files | `/tmp` | Ephemeral |

## Backup Methods

### Automated Backup (Recommended)

#### Using Make Command

```bash
# Full backup
make backup

# Backup to specific directory
make backup BACKUP_DIR=/path/to/backups

# Automated daily backup (cron)
0 2 * * * cd /path/to/OsMEN && make backup
```

#### Manual Backup Script

```bash
#!/bin/bash
# backup.sh - Complete OsMEN backup

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting OsMEN backup to $BACKUP_DIR"

# 1. Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec osmen-postgres pg_dumpall -U postgres > "$BACKUP_DIR/postgres_backup.sql"

# 2. Backup Qdrant
echo "Backing up Qdrant vectors..."
docker exec osmen-qdrant qdrant-backup > "$BACKUP_DIR/qdrant_backup.snapshot"

# 3. Backup configuration
echo "Backing up configuration..."
cp .env "$BACKUP_DIR/env_backup"
cp -r config "$BACKUP_DIR/"

# 4. Backup n8n workflows
echo "Backing up n8n workflows..."
docker cp osmen-n8n:/home/node/.n8n "$BACKUP_DIR/n8n_data"

# 5. Backup Langflow
echo "Backing up Langflow flows..."
cp -r langflow/flows "$BACKUP_DIR/"

# 6. Backup user content
echo "Backing up user content..."
cp -r content "$BACKUP_DIR/"
cp -r obsidian-vault "$BACKUP_DIR/" 2>/dev/null || echo "No Obsidian vault"

# 7. Create backup manifest
echo "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest.json" <<EOF
{
  "timestamp": "$(date -Iseconds)",
  "version": "$(cat VERSION 2>/dev/null || echo 'unknown')",
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

# 8. Compress backup
echo "Compressing backup..."
tar -czf "$BACKUP_DIR.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "✅ Backup complete: $BACKUP_DIR.tar.gz"
```

Save as `scripts/backup.sh` and make executable:
```bash
chmod +x scripts/backup.sh
```

### Incremental Backups

For large installations, use incremental backups:

```bash
#!/bin/bash
# incremental_backup.sh

FULL_BACKUP_DAY=0  # Sunday
TODAY=$(date +%u)   # 1-7 (Monday-Sunday)

if [ "$TODAY" -eq "$FULL_BACKUP_DAY" ]; then
    echo "Performing full backup..."
    ./scripts/backup.sh
else
    echo "Performing incremental backup..."
    # Only backup changed files
    rsync -av --link-dest=../latest backups/latest/ backups/$(date +%Y%m%d)/
fi
```

## Backup Storage

### Local Storage

```bash
# Create backup directory
mkdir -p /mnt/backups/osmen

# Set as backup location
export BACKUP_DIR=/mnt/backups/osmen
```

### Remote Storage

#### AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Upload backup
aws s3 cp backup.tar.gz s3://your-bucket/osmen-backups/

# Automated upload
make backup && \
  aws s3 cp ./backups/latest.tar.gz s3://your-bucket/osmen-backups/$(date +%Y%m%d).tar.gz
```

#### Rsync to Remote Server

```bash
# Backup and sync to remote
make backup
rsync -avz --progress ./backups/ user@backup-server:/backups/osmen/
```

#### Cloud Storage (Rclone)

```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure cloud storage
rclone config

# Upload backup
make backup
rclone copy ./backups/ remote:osmen-backups/
```

## Backup Verification

### Test Backup Integrity

```bash
#!/bin/bash
# verify_backup.sh

BACKUP_FILE="$1"

echo "Verifying backup: $BACKUP_FILE"

# 1. Check file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Backup file not found"
    exit 1
fi

# 2. Check file integrity
if ! tar -tzf "$BACKUP_FILE" > /dev/null 2>&1; then
    echo "❌ Backup file is corrupted"
    exit 1
fi

# 3. List contents
echo "✅ Backup file is valid"
echo "Contents:"
tar -tzf "$BACKUP_FILE" | head -20

# 4. Check size
SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE")
echo "Size: $(numfmt --to=iec-i --suffix=B $SIZE)"

# 5. Extract and verify manifest
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
if [ -f "$TEMP_DIR"/*/manifest.json ]; then
    echo "Manifest:"
    cat "$TEMP_DIR"/*/manifest.json
    rm -rf "$TEMP_DIR"
    echo "✅ Backup verification passed"
    exit 0
else
    echo "⚠️  No manifest found"
    rm -rf "$TEMP_DIR"
    exit 1
fi
```

### Automated Verification

Add to cron after backup:
```cron
0 3 * * * /path/to/scripts/backup.sh && /path/to/scripts/verify_backup.sh /path/to/backups/latest.tar.gz
```

## Recovery Procedures

### Full System Recovery

```bash
#!/bin/bash
# restore.sh - Full system restore

BACKUP_FILE="$1"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: ./restore.sh <backup-file>"
    exit 1
fi

echo "⚠️  WARNING: This will overwrite existing data!"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# 1. Stop all services
echo "Stopping services..."
docker-compose down

# 2. Extract backup
echo "Extracting backup..."
TEMP_DIR=$(mktemp -d)
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"
BACKUP_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d)

# 3. Restore PostgreSQL
echo "Restoring PostgreSQL..."
docker-compose up -d postgres
sleep 10
cat "$BACKUP_DIR/postgres_backup.sql" | docker exec -i osmen-postgres psql -U postgres

# 4. Restore configuration
echo "Restoring configuration..."
cp "$BACKUP_DIR/env_backup" .env
cp -r "$BACKUP_DIR/config" ./

# 5. Restore Qdrant
echo "Restoring Qdrant..."
docker-compose up -d qdrant
sleep 5
cat "$BACKUP_DIR/qdrant_backup.snapshot" | docker exec -i osmen-qdrant qdrant-restore

# 6. Restore n8n
echo "Restoring n8n..."
docker cp "$BACKUP_DIR/n8n_data" osmen-n8n:/home/node/.n8n

# 7. Restore Langflow
echo "Restoring Langflow..."
cp -r "$BACKUP_DIR/flows" langflow/

# 8. Restore user content
echo "Restoring user content..."
cp -r "$BACKUP_DIR/content" ./
cp -r "$BACKUP_DIR/obsidian-vault" ./ 2>/dev/null || true

# 9. Restart all services
echo "Starting all services..."
docker-compose up -d

# 10. Verify
echo "Waiting for services to start..."
sleep 30
python3 check_operational.py

echo "✅ Restore complete"
rm -rf "$TEMP_DIR"
```

### Partial Recovery

#### Restore Only PostgreSQL

```bash
# Extract SQL file
tar -xzf backup.tar.gz --wildcards '*/postgres_backup.sql'

# Restore
cat postgres_backup.sql | docker exec -i osmen-postgres psql -U postgres
```

#### Restore Only Configuration

```bash
# Extract config
tar -xzf backup.tar.gz --wildcards '*/.env' '*/config/*'

# Copy to current directory
cp extracted/.env ./
cp -r extracted/config ./
```

#### Restore Single n8n Workflow

```bash
# Export from backup
tar -xzf backup.tar.gz --wildcards '*/n8n_data/workflows/*'

# Import via n8n UI or CLI
```

## Disaster Recovery Planning

### Recovery Time Objectives (RTO)

| Scenario | Target RTO | Steps |
|----------|-----------|-------|
| Single service failure | 15 minutes | Restart service |
| Data corruption | 1 hour | Restore from last backup |
| Complete system failure | 4 hours | Full restore on new hardware |
| Site disaster | 24 hours | Restore from off-site backup |

### Recovery Point Objectives (RPO)

| Data Type | Target RPO | Backup Frequency |
|-----------|-----------|------------------|
| Database | 1 hour | Hourly |
| Configuration | 1 day | On change + daily |
| User content | 1 day | Daily |
| Workflows | 1 day | Daily |

### Disaster Recovery Checklist

**Preparation:**
- [ ] Document backup procedures
- [ ] Test restore procedures quarterly
- [ ] Maintain off-site backups
- [ ] Keep hardware inventory
- [ ] Document dependencies and credentials

**During Incident:**
- [ ] Assess damage and data loss
- [ ] Identify most recent valid backup
- [ ] Prepare recovery environment
- [ ] Execute restore procedure
- [ ] Verify data integrity

**Post-Recovery:**
- [ ] Document incident
- [ ] Update disaster recovery plan
- [ ] Review backup strategy
- [ ] Test restored system thoroughly

## Backup Rotation

### Grandfather-Father-Son (GFS)

```bash
# Daily backups (kept for 7 days)
DAILY_BACKUP="backups/daily/$(date +%A).tar.gz"

# Weekly backups (kept for 4 weeks)
WEEKLY_BACKUP="backups/weekly/$(date +%U).tar.gz"

# Monthly backups (kept for 12 months)
MONTHLY_BACKUP="backups/monthly/$(date +%B).tar.gz"

# Determine which backup to create
DAY_OF_WEEK=$(date +%u)
DAY_OF_MONTH=$(date +%d)

if [ "$DAY_OF_MONTH" = "01" ]; then
    # Monthly backup
    make backup BACKUP_FILE="$MONTHLY_BACKUP"
elif [ "$DAY_OF_WEEK" = "7" ]; then
    # Weekly backup
    make backup BACKUP_FILE="$WEEKLY_BACKUP"
else
    # Daily backup
    make backup BACKUP_FILE="$DAILY_BACKUP"
fi
```

### Retention Policy

```bash
# Delete old backups
find backups/daily/ -mtime +7 -delete     # Keep 7 days
find backups/weekly/ -mtime +28 -delete   # Keep 4 weeks
find backups/monthly/ -mtime +365 -delete # Keep 12 months
```

## Monitoring and Alerts

### Backup Monitoring Script

```bash
#!/bin/bash
# monitor_backups.sh

BACKUP_DIR="./backups"
MAX_AGE_HOURS=25

LATEST_BACKUP=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)
BACKUP_AGE_HOURS=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 3600 ))

if [ $BACKUP_AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo "⚠️  WARNING: Last backup is $BACKUP_AGE_HOURS hours old!"
    # Send alert (email, Slack, etc.)
    exit 1
else
    echo "✅ Backup is up to date ($BACKUP_AGE_HOURS hours old)"
    exit 0
fi
```

### Integration with Monitoring

**Prometheus:**
```yaml
# prometheus.yml
- job_name: 'osmen_backup'
  static_configs:
    - targets: ['localhost:9090']
  metrics_path: '/metrics/backup'
```

**Grafana Alert:**
- Alert when last backup > 24 hours old
- Alert when backup size changes >20%
- Alert when backup fails

## Cloud Backup Solutions

### Automated Cloud Backup (All-in-One)

```bash
#!/bin/bash
# cloud_backup.sh - Backup to multiple cloud providers

# Backup locally
make backup

LATEST_BACKUP=$(ls -t backups/*.tar.gz | head -1)

# Upload to AWS S3
aws s3 cp "$LATEST_BACKUP" s3://osmen-backups/

# Upload to Google Cloud
gsutil cp "$LATEST_BACKUP" gs://osmen-backups/

# Upload to Azure
az storage blob upload --file "$LATEST_BACKUP" --container osmen-backups

# Verify uploads
echo "✅ Backup uploaded to cloud storage"
```

## Testing Recovery

### Quarterly Recovery Test

**Procedure:**
1. Set up clean test environment
2. Select random backup from last month
3. Perform full restore
4. Verify all services operational
5. Test agent functionality
6. Document any issues
7. Update procedures if needed

**Test Checklist:**
- [ ] Backup extracts successfully
- [ ] Database restores without errors
- [ ] All services start correctly
- [ ] Web UIs accessible
- [ ] Agents execute successfully
- [ ] Data integrity verified
- [ ] Performance acceptable

## Troubleshooting

### Backup Fails

**Issue:** PostgreSQL dump fails  
**Solution:**
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check disk space
df -h

# Manual backup attempt
docker exec osmen-postgres pg_dumpall -U postgres > test_backup.sql
```

### Restore Fails

**Issue:** "Database already exists"  
**Solution:**
```bash
# Drop existing database first
docker exec -it osmen-postgres psql -U postgres -c "DROP DATABASE IF EXISTS osmen_app;"

# Then restore
cat backup.sql | docker exec -i osmen-postgres psql -U postgres
```

### Large Backup Size

**Issue:** Backups too large  
**Solutions:**
- Exclude logs from backup
- Compress with higher ratio: `tar -czf` → `tar -cJf` (xz compression)
- Clean old vector embeddings in Qdrant
- Archive old workflows

## Security Considerations

### Backup Encryption

```bash
# Encrypt backup
gpg --symmetric --cipher-algo AES256 backup.tar.gz

# Decrypt for restore
gpg --decrypt backup.tar.gz.gpg > backup.tar.gz
```

### Secure Storage

- Never store `.env` backups unencrypted
- Use encrypted cloud storage
- Restrict backup file permissions: `chmod 600 backup.tar.gz`
- Keep encryption keys separate from backups
- Rotate encryption keys annually

### Access Control

- Limit who can access backups
- Use separate credentials for backup storage
- Enable MFA on cloud storage accounts
- Audit backup access regularly

## Resources

- **Backup Tools:** rsync, rclone, duplicity, restic
- **Cloud Storage:** AWS S3, Google Cloud Storage, Azure Blob
- **Monitoring:** Prometheus, Grafana, Nagios
- **Encryption:** GPG, OpenSSL, age

---

**Last Updated:** 2024-11-18  
**Review Cycle:** Quarterly  
**Next Review:** 2025-02-18
