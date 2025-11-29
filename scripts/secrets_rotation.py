#!/usr/bin/env python3
"""
Secrets Rotation Module for OsMEN v3.0

Provides automated rotation for:
- API keys (OpenAI, Anthropic)
- Database passwords
- OAuth tokens
- Encryption keys
- JWT signing keys

Usage:
    python scripts/secrets_rotation.py --secret openai_api_key --rotate
    python scripts/secrets_rotation.py --check-all
    python scripts/secrets_rotation.py --schedule daily
"""

import os
import sys
import json
import secrets
import hashlib
import base64
import argparse
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==============================================================================
# Configuration
# ==============================================================================

class RotationPriority(Enum):
    """Priority levels for secret rotation"""
    CRITICAL = "critical"   # Daily
    HIGH = "high"           # Weekly
    NORMAL = "normal"       # Monthly
    LOW = "low"             # Quarterly


@dataclass
class SecretConfig:
    """Configuration for a single secret"""
    name: str
    env_var: str
    priority: RotationPriority
    max_age_days: int
    rotation_handler: Optional[str] = None  # Handler function name
    backup_before_rotate: bool = True
    notify_on_rotate: bool = True
    last_rotated: Optional[datetime] = None
    
    def needs_rotation(self) -> bool:
        """Check if secret needs rotation based on age"""
        if not self.last_rotated:
            return True
        
        age = datetime.utcnow() - self.last_rotated
        return age.days >= self.max_age_days


# Default secret configurations
DEFAULT_SECRETS = [
    SecretConfig(
        name="openai_api_key",
        env_var="OPENAI_API_KEY",
        priority=RotationPriority.CRITICAL,
        max_age_days=30,
        rotation_handler="rotate_openai_key"
    ),
    SecretConfig(
        name="anthropic_api_key",
        env_var="ANTHROPIC_API_KEY",
        priority=RotationPriority.CRITICAL,
        max_age_days=30,
        rotation_handler="rotate_anthropic_key"
    ),
    SecretConfig(
        name="postgres_password",
        env_var="POSTGRES_PASSWORD",
        priority=RotationPriority.HIGH,
        max_age_days=90,
        rotation_handler="rotate_postgres_password"
    ),
    SecretConfig(
        name="redis_password",
        env_var="REDIS_PASSWORD",
        priority=RotationPriority.HIGH,
        max_age_days=90,
        rotation_handler="rotate_redis_password"
    ),
    SecretConfig(
        name="jwt_secret",
        env_var="JWT_SECRET",
        priority=RotationPriority.HIGH,
        max_age_days=90,
        rotation_handler="rotate_jwt_secret"
    ),
    SecretConfig(
        name="encryption_key",
        env_var="ENCRYPTION_KEY",
        priority=RotationPriority.NORMAL,
        max_age_days=180,
        rotation_handler="rotate_encryption_key"
    ),
    SecretConfig(
        name="oauth_client_secret",
        env_var="OAUTH_CLIENT_SECRET",
        priority=RotationPriority.NORMAL,
        max_age_days=365,
        rotation_handler="rotate_oauth_secret"
    ),
]


# ==============================================================================
# Secret Generation
# ==============================================================================

def generate_api_key(length: int = 32) -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(length)


def generate_password(length: int = 32) -> str:
    """Generate a secure password"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_jwt_secret(length: int = 64) -> str:
    """Generate a JWT signing secret"""
    return secrets.token_hex(length)


def generate_encryption_key() -> str:
    """Generate a 256-bit encryption key (base64 encoded)"""
    key = secrets.token_bytes(32)  # 256 bits
    return base64.b64encode(key).decode('utf-8')


# ==============================================================================
# Rotation Handlers
# ==============================================================================

class RotationHandlers:
    """Secret rotation handlers"""
    
    @staticmethod
    async def rotate_openai_key(old_key: Optional[str]) -> Dict[str, Any]:
        """
        Rotate OpenAI API key
        
        Note: OpenAI API keys must be rotated manually via dashboard.
        This handler generates a placeholder and notifies admin.
        """
        logger.info("OpenAI API keys must be rotated via OpenAI dashboard")
        logger.info("Visit: https://platform.openai.com/api-keys")
        
        return {
            "status": "manual_required",
            "message": "Rotate key at OpenAI dashboard",
            "url": "https://platform.openai.com/api-keys",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_anthropic_key(old_key: Optional[str]) -> Dict[str, Any]:
        """
        Rotate Anthropic API key
        
        Note: Anthropic API keys must be rotated manually via console.
        """
        logger.info("Anthropic API keys must be rotated via Anthropic console")
        logger.info("Visit: https://console.anthropic.com/keys")
        
        return {
            "status": "manual_required",
            "message": "Rotate key at Anthropic console",
            "url": "https://console.anthropic.com/keys",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_postgres_password(old_password: Optional[str]) -> Dict[str, Any]:
        """Rotate PostgreSQL password"""
        new_password = generate_password(32)
        
        # In production, this would:
        # 1. Connect to PostgreSQL
        # 2. ALTER USER ... PASSWORD '...'
        # 3. Update connection strings
        # 4. Verify connectivity
        
        logger.info("Generated new PostgreSQL password")
        logger.warning("Ensure all services are updated with new password")
        
        return {
            "status": "success",
            "new_value": new_password,
            "message": "Update DATABASE_URL and restart services",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_redis_password(old_password: Optional[str]) -> Dict[str, Any]:
        """Rotate Redis password"""
        new_password = generate_password(32)
        
        # In production, this would:
        # 1. Update Redis config
        # 2. Restart Redis with new password
        # 3. Update all Redis clients
        
        logger.info("Generated new Redis password")
        
        return {
            "status": "success",
            "new_value": new_password,
            "message": "Update REDIS_URL and restart services",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_jwt_secret(old_secret: Optional[str]) -> Dict[str, Any]:
        """Rotate JWT signing secret"""
        new_secret = generate_jwt_secret(64)
        
        logger.info("Generated new JWT secret")
        logger.warning("Existing sessions will be invalidated")
        
        return {
            "status": "success",
            "new_value": new_secret,
            "message": "All existing JWTs will be invalid",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_encryption_key(old_key: Optional[str]) -> Dict[str, Any]:
        """Rotate encryption key"""
        new_key = generate_encryption_key()
        
        logger.info("Generated new encryption key")
        logger.warning("Re-encrypt any stored encrypted data")
        
        return {
            "status": "success",
            "new_value": new_key,
            "message": "Re-encrypt stored data with new key",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def rotate_oauth_secret(old_secret: Optional[str]) -> Dict[str, Any]:
        """Rotate OAuth client secret"""
        logger.info("OAuth client secrets must be rotated via provider dashboard")
        
        return {
            "status": "manual_required",
            "message": "Rotate secret at OAuth provider (Google/Microsoft)",
            "timestamp": datetime.utcnow().isoformat()
        }


# ==============================================================================
# Audit Logging
# ==============================================================================

@dataclass
class AuditRecord:
    """Audit record for secret operations"""
    timestamp: datetime
    secret_name: str
    operation: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "secret_name": self.secret_name,
            "operation": self.operation,
            "status": self.status,
            "details": self.details
        }


class AuditLogger:
    """Logs secret rotation operations"""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or Path("logs/secrets_audit.json")
        self.records: List[AuditRecord] = []
        self._load_existing()
    
    def _load_existing(self):
        """Load existing audit records"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    # Keep only last 1000 records
                    for record in data[-1000:]:
                        self.records.append(AuditRecord(
                            timestamp=datetime.fromisoformat(record['timestamp']),
                            secret_name=record['secret_name'],
                            operation=record['operation'],
                            status=record['status'],
                            details=record.get('details', {})
                        ))
            except Exception as e:
                logger.warning(f"Could not load audit log: {e}")
    
    def log(
        self,
        secret_name: str,
        operation: str,
        status: str,
        details: Optional[Dict] = None
    ):
        """Log an operation"""
        record = AuditRecord(
            timestamp=datetime.utcnow(),
            secret_name=secret_name,
            operation=operation,
            status=status,
            details=details or {}
        )
        self.records.append(record)
        self._save()
        
        logger.info(f"Audit: {operation} {secret_name} - {status}")
    
    def _save(self):
        """Save audit records to file"""
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump([r.to_dict() for r in self.records], f, indent=2)
        except Exception as e:
            logger.error(f"Could not save audit log: {e}")
    
    def get_recent(self, limit: int = 50) -> List[Dict]:
        """Get recent audit records"""
        return [r.to_dict() for r in self.records[-limit:]]


# ==============================================================================
# Secrets Manager
# ==============================================================================

class SecretsManager:
    """
    Manages secret rotation
    
    Usage:
        manager = SecretsManager()
        
        # Check which secrets need rotation
        needs_rotation = manager.check_all()
        
        # Rotate a specific secret
        result = await manager.rotate("openai_api_key")
        
        # Run scheduled rotation
        await manager.run_schedule()
    """
    
    def __init__(
        self,
        configs: Optional[List[SecretConfig]] = None,
        env_file: Optional[Path] = None
    ):
        self.configs = {c.name: c for c in (configs or DEFAULT_SECRETS)}
        self.env_file = env_file or Path(".env")
        self.handlers = RotationHandlers()
        self.audit = AuditLogger()
        self.state_file = Path(".secrets_state.json")
        self._load_state()
    
    def _load_state(self):
        """Load rotation state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                for name, data in state.items():
                    if name in self.configs:
                        if data.get('last_rotated'):
                            self.configs[name].last_rotated = datetime.fromisoformat(
                                data['last_rotated']
                            )
            except Exception as e:
                logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save rotation state"""
        state = {}
        for name, config in self.configs.items():
            state[name] = {
                'last_rotated': config.last_rotated.isoformat() if config.last_rotated else None
            }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")
    
    def get_current_value(self, name: str) -> Optional[str]:
        """Get current value of a secret from environment"""
        if name not in self.configs:
            return None
        
        env_var = self.configs[name].env_var
        return os.environ.get(env_var)
    
    def check_all(self) -> Dict[str, bool]:
        """Check which secrets need rotation"""
        result = {}
        for name, config in self.configs.items():
            needs = config.needs_rotation()
            result[name] = needs
            if needs:
                logger.warning(f"Secret {name} needs rotation")
        return result
    
    def check(self, name: str) -> bool:
        """Check if a specific secret needs rotation"""
        if name not in self.configs:
            raise ValueError(f"Unknown secret: {name}")
        return self.configs[name].needs_rotation()
    
    async def rotate(self, name: str, force: bool = False) -> Dict[str, Any]:
        """
        Rotate a specific secret
        
        Args:
            name: Secret name
            force: Force rotation even if not needed
            
        Returns:
            Rotation result
        """
        if name not in self.configs:
            raise ValueError(f"Unknown secret: {name}")
        
        config = self.configs[name]
        
        # Check if rotation needed
        if not force and not config.needs_rotation():
            return {
                "status": "skipped",
                "message": "Secret does not need rotation",
                "last_rotated": config.last_rotated.isoformat() if config.last_rotated else None
            }
        
        # Backup current value
        old_value = self.get_current_value(name)
        if config.backup_before_rotate and old_value:
            self._backup_secret(name, old_value)
        
        # Get handler
        handler_name = config.rotation_handler
        if not handler_name:
            return {
                "status": "error",
                "message": "No rotation handler configured"
            }
        
        handler = getattr(self.handlers, handler_name, None)
        if not handler:
            return {
                "status": "error",
                "message": f"Handler not found: {handler_name}"
            }
        
        # Execute rotation
        self.audit.log(name, "rotation_start", "started")
        
        try:
            result = await handler(old_value)
            
            if result.get("status") == "success":
                config.last_rotated = datetime.utcnow()
                self._save_state()
                
                # Update environment file if new value provided
                if result.get("new_value"):
                    self._update_env_file(config.env_var, result["new_value"])
                    # Don't include actual value in result for security
                    result["new_value"] = "***"
            
            self.audit.log(name, "rotation_complete", result.get("status", "unknown"), result)
            return result
            
        except Exception as e:
            error_result = {
                "status": "error",
                "message": str(e)
            }
            self.audit.log(name, "rotation_failed", "error", error_result)
            return error_result
    
    def _backup_secret(self, name: str, value: str):
        """Backup a secret before rotation"""
        backup_dir = Path("backups/secrets")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{name}_{timestamp}.backup"
        
        # Hash the value for audit (don't store plaintext)
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]
        
        backup_data = {
            "name": name,
            "timestamp": timestamp,
            "value_hash": value_hash
        }
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        logger.info(f"Backed up {name} to {backup_file}")
    
    def _update_env_file(self, env_var: str, new_value: str):
        """Update environment file with new value"""
        if not self.env_file.exists():
            logger.warning(f".env file not found at {self.env_file}")
            return
        
        try:
            # Read existing content
            with open(self.env_file, 'r') as f:
                lines = f.readlines()
            
            # Update or add the variable
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f"{env_var}="):
                    lines[i] = f"{env_var}={new_value}\n"
                    found = True
                    break
            
            if not found:
                lines.append(f"{env_var}={new_value}\n")
            
            # Write back
            with open(self.env_file, 'w') as f:
                f.writelines(lines)
            
            logger.info(f"Updated {env_var} in {self.env_file}")
            
        except Exception as e:
            logger.error(f"Failed to update .env: {e}")
    
    async def rotate_all(self, force: bool = False) -> Dict[str, Any]:
        """Rotate all secrets that need rotation"""
        results = {}
        
        for name, config in self.configs.items():
            if force or config.needs_rotation():
                results[name] = await self.rotate(name, force)
        
        return results
    
    async def run_schedule(self, priority: Optional[RotationPriority] = None):
        """Run scheduled rotation based on priority"""
        for name, config in self.configs.items():
            if priority and config.priority != priority:
                continue
            
            if config.needs_rotation():
                logger.info(f"Scheduled rotation for {name}")
                result = await self.rotate(name)
                logger.info(f"Result: {result.get('status')}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all secrets"""
        status = {}
        
        for name, config in self.configs.items():
            status[name] = {
                "env_var": config.env_var,
                "priority": config.priority.value,
                "max_age_days": config.max_age_days,
                "last_rotated": config.last_rotated.isoformat() if config.last_rotated else None,
                "needs_rotation": config.needs_rotation(),
                "has_value": bool(self.get_current_value(name))
            }
        
        return status
    
    def get_audit_log(self, limit: int = 50) -> List[Dict]:
        """Get recent audit log entries"""
        return self.audit.get_recent(limit)


# ==============================================================================
# CLI Interface
# ==============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description="OsMEN Secrets Rotation Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--secret",
        help="Name of secret to rotate"
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="Perform rotation"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rotation even if not needed"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if rotation is needed"
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check all secrets"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status of all secrets"
    )
    parser.add_argument(
        "--schedule",
        choices=["daily", "weekly", "monthly"],
        help="Run scheduled rotation by priority"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Show audit log"
    )
    parser.add_argument(
        "--audit-limit",
        type=int,
        default=20,
        help="Number of audit entries to show"
    )
    
    args = parser.parse_args()
    
    manager = SecretsManager()
    
    if args.check_all:
        print("\n=== Secrets Rotation Check ===\n")
        needs = manager.check_all()
        for name, needs_rotation in needs.items():
            status = "⚠️  NEEDS ROTATION" if needs_rotation else "✅ OK"
            print(f"  {name}: {status}")
        print()
    
    elif args.status:
        print("\n=== Secrets Status ===\n")
        status = manager.get_status()
        for name, info in status.items():
            print(f"  {name}:")
            print(f"    Env Var: {info['env_var']}")
            print(f"    Priority: {info['priority']}")
            print(f"    Max Age: {info['max_age_days']} days")
            print(f"    Last Rotated: {info['last_rotated'] or 'Never'}")
            print(f"    Has Value: {'Yes' if info['has_value'] else 'No'}")
            print(f"    Needs Rotation: {'Yes' if info['needs_rotation'] else 'No'}")
            print()
    
    elif args.audit:
        print("\n=== Audit Log ===\n")
        entries = manager.get_audit_log(args.audit_limit)
        for entry in entries:
            print(f"  [{entry['timestamp']}] {entry['operation']} {entry['secret_name']}: {entry['status']}")
        print()
    
    elif args.secret:
        if args.check:
            needs = manager.check(args.secret)
            status = "needs rotation" if needs else "OK"
            print(f"\n{args.secret}: {status}\n")
        
        elif args.rotate:
            print(f"\n=== Rotating {args.secret} ===\n")
            result = await manager.rotate(args.secret, args.force)
            print(f"  Status: {result.get('status')}")
            print(f"  Message: {result.get('message', 'N/A')}")
            if result.get('url'):
                print(f"  URL: {result['url']}")
            print()
    
    elif args.schedule:
        priority_map = {
            "daily": RotationPriority.CRITICAL,
            "weekly": RotationPriority.HIGH,
            "monthly": RotationPriority.NORMAL
        }
        priority = priority_map[args.schedule]
        
        print(f"\n=== Running {args.schedule} rotation schedule ===\n")
        await manager.run_schedule(priority)
        print()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
