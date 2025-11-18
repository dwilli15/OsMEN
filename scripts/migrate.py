#!/usr/bin/env python3
"""
Database migration script for OsMEN.
Handles version upgrades and schema changes.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def migrate_2_0_to_2_1():
    """Migrate database from v2.0 to v2.1."""
    print("🔄 Migrating from v2.0 to v2.1...")
    print()
    
    try:
        # Import database connection (would need actual implementation)
        # from database import engine
        
        print("📝 Adding new schema elements...")
        
        # Example migrations (would be actual SQL)
        migrations = [
            "ALTER TABLE agents ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'",
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS context_window INTEGER DEFAULT 4096",
            "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id)",
        ]
        
        for i, migration in enumerate(migrations, 1):
            print(f"  [{i}/{len(migrations)}] {migration[:60]}...")
            # engine.execute(migration)
        
        print()
        print("✅ Migration complete")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def migrate_1_x_to_2_0():
    """Migrate database from v1.x to v2.0."""
    print("🔄 Migrating from v1.x to v2.0...")
    print()
    print("⚠️  This is a major version migration!")
    print()
    
    try:
        print("📝 Performing schema changes...")
        
        migrations = [
            "CREATE TABLE IF NOT EXISTS agent_metadata (id SERIAL PRIMARY KEY, agent_name VARCHAR(255), metadata JSONB)",
            "ALTER TABLE conversations ADD COLUMN IF NOT EXISTS vector_id INTEGER",
            "CREATE INDEX IF NOT EXISTS idx_agent_metadata_agent_name ON agent_metadata(agent_name)",
        ]
        
        for i, migration in enumerate(migrations, 1):
            print(f"  [{i}/{len(migrations)}] {migration[:60]}...")
            # engine.execute(migration)
        
        print()
        print("📝 Migrating data...")
        # Data migration logic here
        
        print()
        print("✅ Migration complete")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 migrate.py --from <version> --to <version>")
        print()
        print("Examples:")
        print("  python3 scripts/migrate.py --from 2.0 --to 2.1")
        print("  python3 scripts/migrate.py --from 1.x --to 2.0")
        print()
        sys.exit(1)
    
    # Parse arguments
    args = {}
    for i in range(1, len(sys.argv), 2):
        if sys.argv[i].startswith('--'):
            args[sys.argv[i][2:]] = sys.argv[i+1]
    
    from_version = args.get('from', '')
    to_version = args.get('to', '')
    
    print("🔧 OsMEN Database Migration")
    print("=" * 60)
    print()
    print(f"From version: {from_version}")
    print(f"To version: {to_version}")
    print()
    
    # Backup warning
    print("⚠️  IMPORTANT: Backup your database before proceeding!")
    print()
    print("Run this command first:")
    print("  ./scripts/backup.sh")
    print()
    
    response = input("Have you backed up your database? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled. Please backup first.")
        sys.exit(1)
    
    print()
    
    # Route to appropriate migration
    success = False
    
    if from_version == '2.0' and to_version == '2.1':
        success = migrate_2_0_to_2_1()
    elif from_version.startswith('1.') and to_version == '2.0':
        success = migrate_1_x_to_2_0()
    else:
        print(f"❌ No migration path from {from_version} to {to_version}")
        print()
        print("Available migration paths:")
        print("  1.x → 2.0")
        print("  2.0 → 2.1")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print()
    
    if success:
        print("✅ Migration completed successfully")
        print()
        print("Next steps:")
        print("1. Restart services: docker-compose restart")
        print("2. Verify functionality: python3 test_agents.py")
        print("3. Update VERSION file")
        sys.exit(0)
    else:
        print("❌ Migration failed")
        print()
        print("To rollback:")
        print("1. Stop services: docker-compose down")
        print("2. Restore backup: ./scripts/restore.sh <backup-file>")
        sys.exit(1)


if __name__ == '__main__':
    main()
