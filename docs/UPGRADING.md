# Upgrade and Migration Guide

Guide for upgrading OsMEN between versions and migrating data safely.

## Version Support Policy

- **Current Version:** 2.0.x
- **Supported Versions:** 2.0.x, 1.x.x
- **Support Duration:** 12 months from release
- **Security Patches:** 18 months from release

## Semantic Versioning

OsMEN follows [Semantic Versioning](https://semver.org/):

- **Major (X.0.0):** Breaking changes, may require manual migration
- **Minor (2.X.0):** New features, backward compatible
- **Patch (2.0.X):** Bug fixes, fully backward compatible

## Before Upgrading

### Pre-Upgrade Checklist

- [ ] **Backup everything** (see [BACKUP_RECOVERY.md](BACKUP_RECOVERY.md))
- [ ] Read release notes and CHANGELOG.md
- [ ] Check compatibility requirements
- [ ] Test upgrade in non-production environment
- [ ] Plan for downtime (if required)
- [ ] Review breaking changes
- [ ] Update dependencies

### Check Current Version

```bash
# Check current version
cat VERSION

# Or check from Docker
docker exec osmen-gateway cat /app/VERSION

# Check all service versions
docker-compose ps
```

## Upgrade Procedures

### Patch Upgrade (2.0.0 → 2.0.1)

**Risk Level:** Low  
**Downtime:** None (rolling restart)  
**Backup Required:** Recommended

```bash
# 1. Backup (recommended)
make backup

# 2. Pull latest version
git fetch origin
git checkout v2.0.1

# 3. Pull new Docker images
docker-compose pull

# 4. Restart services
docker-compose up -d

# 5. Verify
python3 check_operational.py
```

**Rollback if needed:**
```bash
git checkout v2.0.0
docker-compose up -d
```

### Minor Upgrade (2.0.0 → 2.1.0)

**Risk Level:** Medium  
**Downtime:** 5-15 minutes  
**Backup Required:** Mandatory

```bash
# 1. MANDATORY BACKUP
make backup

# 2. Read release notes
cat docs/RELEASE_NOTES_v2.1.md

# 3. Stop services
docker-compose down

# 4. Update code
git fetch origin
git checkout v2.1.0

# 5. Update dependencies
pip install -r requirements.txt

# 6. Run migrations
python3 scripts/migrate.py --from 2.0 --to 2.1

# 7. Update configuration
# Review .env.example for new settings
diff .env .env.example

# 8. Pull new images
docker-compose pull

# 9. Start services
docker-compose up -d

# 10. Run post-upgrade checks
python3 scripts/post_upgrade_check.py

# 11. Verify
python3 check_operational.py
```

### Major Upgrade (1.x → 2.0.0)

**Risk Level:** High  
**Downtime:** 30-60 minutes  
**Backup Required:** Mandatory  
**Testing Required:** Mandatory

```bash
# 1. MANDATORY: Full backup
make backup

# 2. Read migration guide
cat docs/MIGRATION_1.x_TO_2.0.md

# 3. Test in staging first
# DO NOT proceed without testing!

# 4. Stop all services
docker-compose down

# 5. Backup database explicitly
docker exec osmen-postgres pg_dumpall -U postgres > backup_v1_final.sql

# 6. Update code
git fetch origin
git checkout v2.0.0

# 7. Review breaking changes
cat CHANGELOG.md | grep "BREAKING"

# 8. Update configuration
# Major versions may require config changes
cp .env .env.v1.backup
# Edit .env with new required settings

# 9. Run data migration
python3 scripts/migrate_v1_to_v2.py

# 10. Update Docker Compose
# docker-compose.yml may have changed
docker-compose config  # Validate

# 11. Pull new images
docker-compose pull

# 12. Start services
docker-compose up -d

# 13. Run extensive checks
python3 scripts/post_upgrade_check.py --full

# 14. Verify all agents
python3 test_agents.py

# 15. Monitor logs
docker-compose logs -f
```

## Migration Scripts

### Database Migration

```python
# scripts/migrate.py
import sys
from sqlalchemy import create_engine

def migrate_2_0_to_2_1(engine):
    """Migrate database from v2.0 to v2.1"""
    
    # Add new columns
    engine.execute("""
        ALTER TABLE agents 
        ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'
    """)
    
    # Update existing data
    engine.execute("""
        UPDATE agents 
        SET metadata = '{"version": "2.1"}'
        WHERE metadata IS NULL
    """)
    
    print("✅ Database migration complete")

if __name__ == "__main__":
    from_version = sys.argv[1]
    to_version = sys.argv[2]
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    if from_version == "2.0" and to_version == "2.1":
        migrate_2_0_to_2_1(engine)
    else:
        print(f"❌ No migration path from {from_version} to {to_version}")
        sys.exit(1)
```

### Configuration Migration

```bash
# scripts/migrate_config.sh
#!/bin/bash

OLD_VERSION=$1
NEW_VERSION=$2

echo "Migrating configuration from $OLD_VERSION to $NEW_VERSION"

# Backup current config
cp .env .env.backup.$OLD_VERSION

# Add new required settings for v2.1
if [ "$NEW_VERSION" = "2.1" ]; then
    echo "# New in v2.1" >> .env
    echo "NEW_FEATURE_ENABLED=true" >> .env
fi

echo "✅ Configuration migration complete"
echo "⚠️  Please review .env for new settings"
```

## Breaking Changes by Version

### v2.0.0 Breaking Changes

**API Changes:**
- `POST /api/agents/execute` → `POST /api/v1/agents/{agent}/execute`
- Response format changed: `{"output": "..."}` → `{"result": {"output": "..."}}`

**Configuration:**
- `LLM_PROVIDER` split into individual provider settings
- `AGENT_MEMORY` renamed to `QDRANT_HOST`

**Database:**
- `conversations` table schema updated
- New `agent_metadata` table added

**Migration Steps:**
1. Update API clients to use new endpoints
2. Update .env with new variable names
3. Run database migration script

### v1.5.0 Breaking Changes

**Dependencies:**
- Python 3.10+ now required (was 3.9+)
- Docker Compose v2 required (was v1)

**Features:**
- Legacy agent system removed
- Workflow triggers changed format

## Rollback Procedures

### Quick Rollback (Within 24 Hours)

If upgrade fails and backup is recent:

```bash
# 1. Stop services
docker-compose down

# 2. Revert code
git checkout v{previous-version}

# 3. Restore backup
./scripts/restore.sh backups/backup_before_upgrade.tar.gz

# 4. Start services
docker-compose up -d

# 5. Verify
python3 check_operational.py
```

### Full Rollback (Older Backup)

```bash
# 1. Stop everything
docker-compose down

# 2. Remove current data
docker volume rm $(docker volume ls -q | grep osmen)

# 3. Revert code to old version
git checkout v{old-version}

# 4. Restore full backup
./scripts/restore.sh backups/{old-backup}.tar.gz

# 5. Verify backup integrity
./scripts/verify_backup.sh

# 6. Start services
docker-compose up -d

# 7. Extensive testing
python3 test_agents.py
```

## Version Compatibility Matrix

### Database Compatibility

| From Version | To Version | Migration Required | Downtime |
|-------------|-----------|-------------------|----------|
| 2.0.x | 2.0.y | No | None |
| 2.0.x | 2.1.x | Yes | 15 min |
| 1.x.x | 2.0.x | Yes | 60 min |
| <1.0 | Any | Not Supported | N/A |

### API Compatibility

| Version | API v1 | API v2 | Notes |
|---------|--------|--------|-------|
| 2.1.x | ✅ | ✅ | Both supported |
| 2.0.x | ✅ | ❌ | API v1 only |
| 1.x.x | ❌ | ❌ | Legacy API |

### Client Compatibility

| Client Version | Server 2.0.x | Server 2.1.x |
|---------------|-------------|-------------|
| 2.1.x | ⚠️ Partial | ✅ Full |
| 2.0.x | ✅ Full | ⚠️ Partial |
| 1.x.x | ❌ No | ❌ No |

## Post-Upgrade Verification

### Verification Checklist

```bash
# Run automated checks
python3 scripts/post_upgrade_check.py

# Manual verification
- [ ] All services running
- [ ] Database accessible
- [ ] Agents execute successfully
- [ ] Workflows trigger correctly
- [ ] API endpoints respond
- [ ] Web UI accessible
- [ ] Memory/vector search works
- [ ] Integrations functional
```

### Test Script

```python
# scripts/post_upgrade_check.py
def verify_upgrade():
    checks = []
    
    # Check services
    checks.append(check_service_health())
    
    # Check database
    checks.append(check_database_schema())
    
    # Check agents
    checks.append(check_agents_execute())
    
    # Check API
    checks.append(check_api_endpoints())
    
    if all(checks):
        print("✅ All post-upgrade checks passed")
        return True
    else:
        print("❌ Some checks failed")
        return False

if __name__ == "__main__":
    success = verify_upgrade()
    sys.exit(0 if success else 1)
```

## Gradual Rollout Strategy

For large deployments:

### Blue-Green Deployment

```bash
# 1. Deploy new version to "green" environment
docker-compose -f docker-compose.green.yml up -d

# 2. Test green environment
curl http://green.internal:8080/health

# 3. Switch load balancer to green
# Update nginx/load balancer config

# 4. Monitor for issues

# 5. If stable, shut down blue
# If problems, switch back to blue
```

### Canary Deployment

```bash
# 1. Deploy new version with 10% traffic
# Update load balancer to send 10% to new version

# 2. Monitor metrics
# - Error rates
# - Response times
# - Resource usage

# 3. Gradually increase traffic
# 10% → 25% → 50% → 100%

# 4. Rollback at any sign of issues
```

## Troubleshooting Upgrades

### Common Issues

**Issue:** Database migration fails

**Solution:**
```bash
# Check migration logs
cat logs/migration.log

# Rollback and try again
./scripts/rollback_migration.py

# Re-run migration with verbose logging
python3 scripts/migrate.py --verbose
```

**Issue:** Services won't start after upgrade

**Solution:**
```bash
# Check logs
docker-compose logs

# Verify configuration
docker-compose config

# Check for port conflicts
netstat -tulpn

# Restart services one by one
docker-compose up -d postgres
docker-compose up -d qdrant
# etc.
```

**Issue:** API compatibility errors

**Solution:**
```bash
# Check API version
curl http://localhost:8080/version

# Update client libraries
pip install --upgrade osmen-client

# Review API changelog
cat docs/API_CHANGELOG.md
```

## Long-Term Support (LTS)

### LTS Versions

| Version | Release Date | End of Support | Notes |
|---------|-------------|----------------|-------|
| 2.0 LTS | 2024-11-01 | 2025-11-01 | Current |
| 1.0 LTS | 2023-06-01 | 2024-06-01 | Ended |

### Support Levels

**Active:** Full support, regular updates  
**Maintenance:** Security fixes only  
**End of Life:** No support

## Resources

- [CHANGELOG.md](../CHANGELOG.md) - All version changes
- [Release Notes](../docs/RELEASE_NOTES_v2.0.md) - Detailed release info
- [Backup Guide](BACKUP_RECOVERY.md) - Backup procedures
- [GitHub Releases](https://github.com/dwilli15/OsMEN/releases) - Download versions

## Getting Help

- **Upgrade Issues:** [GitHub Issues](https://github.com/dwilli15/OsMEN/issues)
- **Questions:** [GitHub Discussions](https://github.com/dwilli15/OsMEN/discussions)
- **Critical Issues:** support@osmen.dev

---

**Last Updated:** 2024-11-18  
**Current Version:** 2.0.0  
**Next Major Release:** 3.0.0 (Q2 2025)
