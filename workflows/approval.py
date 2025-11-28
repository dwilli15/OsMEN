"""
Approval Gating System for OsMEN Workflows

Provides human-in-the-loop approval for sensitive operations.
Supports configurable approval rules, timeouts, and escalation.

Usage:
    from workflows.approval import ApprovalGate, ApprovalRule
    
    # Create approval gate
    gate = ApprovalGate()
    
    # Define rules
    gate.add_rule(ApprovalRule(
        name="sensitive_email",
        pattern="send_email",
        requires_approval=True,
        timeout_seconds=300
    ))
    
    # Check if approval needed
    needs_approval = await gate.check("send_email", {"to": "external@domain.com"})
    
    # Request approval
    if needs_approval:
        approved = await gate.request_approval(
            run_id="...",
            action="send_email",
            context={"to": "external@domain.com", "subject": "..."}
        )
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


class ApprovalStatus(str, Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    AUTO_APPROVED = "auto_approved"
    ESCALATED = "escalated"


class RiskLevel(str, Enum):
    """Risk level for operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRule:
    """
    Rule for when approval is required.
    
    Attributes:
        name: Rule name for identification
        pattern: Regex pattern to match action names
        requires_approval: Whether approval is needed
        risk_level: Risk level of matching actions
        timeout_seconds: Time to wait for approval
        auto_approve_after: Auto-approve if no response (None = never)
        escalate_to: Who to escalate to on timeout
        conditions: Additional conditions (callable returning bool)
        bypass_roles: Roles that can bypass this rule
    """
    name: str
    pattern: str
    requires_approval: bool = True
    risk_level: RiskLevel = RiskLevel.MEDIUM
    timeout_seconds: int = 300
    auto_approve_after: Optional[int] = None
    escalate_to: Optional[str] = None
    conditions: Optional[Callable[[str, Dict], bool]] = None
    bypass_roles: Set[str] = field(default_factory=set)
    
    def matches(self, action: str, context: Dict[str, Any]) -> bool:
        """Check if this rule matches the action"""
        if not re.match(self.pattern, action):
            return False
        
        if self.conditions:
            return self.conditions(action, context)
        
        return True


@dataclass
class ApprovalRequest:
    """A pending approval request"""
    id: str
    run_id: str
    action: str
    context: Dict[str, Any]
    rule_name: str
    risk_level: RiskLevel
    status: ApprovalStatus
    created_at: datetime
    timeout_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_reason: Optional[str] = None
    escalation_chain: List[str] = field(default_factory=list)


class ApprovalGate:
    """
    Manages approval rules and requests.
    
    Supports:
    - Rule-based approval requirements
    - Timeout and auto-approval
    - Escalation chains
    - Bypass for trusted roles
    - Webhook notifications
    """
    
    def __init__(self):
        self._rules: List[ApprovalRule] = []
        self._pending: Dict[str, ApprovalRequest] = {}
        self._history: List[ApprovalRequest] = []
        self._approval_waiters: Dict[str, asyncio.Event] = {}
        self._approval_results: Dict[str, bool] = {}
        
        # Notification handlers
        self._on_request_handlers: List[Callable[[ApprovalRequest], None]] = []
        self._on_response_handlers: List[Callable[[ApprovalRequest], None]] = []
        
        # Default rules
        self._add_default_rules()
    
    def _add_default_rules(self):
        """Add sensible default approval rules"""
        
        # Email to external domains
        self.add_rule(ApprovalRule(
            name="external_email",
            pattern=r"send_email.*",
            risk_level=RiskLevel.MEDIUM,
            timeout_seconds=300,
            conditions=lambda a, c: self._is_external_email(c)
        ))
        
        # File writes outside safe directories
        self.add_rule(ApprovalRule(
            name="unsafe_file_write",
            pattern=r"write_file.*",
            risk_level=RiskLevel.HIGH,
            timeout_seconds=180,
            conditions=lambda a, c: self._is_unsafe_path(c)
        ))
        
        # Shell commands
        self.add_rule(ApprovalRule(
            name="shell_command",
            pattern=r"execute_shell.*",
            risk_level=RiskLevel.CRITICAL,
            timeout_seconds=120,
            requires_approval=True
        ))
        
        # Calendar event creation
        self.add_rule(ApprovalRule(
            name="calendar_event",
            pattern=r"create_calendar_event.*",
            risk_level=RiskLevel.LOW,
            timeout_seconds=60,
            auto_approve_after=30  # Auto-approve after 30s if no response
        ))
        
        # Database modifications
        self.add_rule(ApprovalRule(
            name="database_write",
            pattern=r"(insert|update|delete)_.*",
            risk_level=RiskLevel.HIGH,
            timeout_seconds=180
        ))
        
        # API calls to external services
        self.add_rule(ApprovalRule(
            name="external_api",
            pattern=r"call_external_api.*",
            risk_level=RiskLevel.MEDIUM,
            timeout_seconds=120
        ))
    
    def _is_external_email(self, context: Dict[str, Any]) -> bool:
        """Check if email is to external domain"""
        to = context.get("to", "")
        internal_domains = {"company.com", "internal.org"}  # Configure as needed
        
        if isinstance(to, list):
            return any(not any(domain in addr for domain in internal_domains) for addr in to)
        return not any(domain in to for domain in internal_domains)
    
    def _is_unsafe_path(self, context: Dict[str, Any]) -> bool:
        """Check if file path is outside safe directories"""
        path = context.get("path", "")
        safe_dirs = {"/tmp", "/home", "/var/data"}  # Configure as needed
        return not any(path.startswith(safe) for safe in safe_dirs)
    
    def add_rule(self, rule: ApprovalRule):
        """Add an approval rule"""
        self._rules.append(rule)
        logger.debug(f"Added approval rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove an approval rule by name"""
        self._rules = [r for r in self._rules if r.name != rule_name]
    
    def get_rules(self) -> List[ApprovalRule]:
        """Get all approval rules"""
        return self._rules.copy()
    
    def on_request(self, handler: Callable[[ApprovalRequest], None]):
        """Register handler for new approval requests"""
        self._on_request_handlers.append(handler)
    
    def on_response(self, handler: Callable[[ApprovalRequest], None]):
        """Register handler for approval responses"""
        self._on_response_handlers.append(handler)
    
    async def check(
        self,
        action: str,
        context: Dict[str, Any],
        user_roles: Optional[Set[str]] = None
    ) -> Optional[ApprovalRule]:
        """
        Check if approval is required for an action.
        
        Args:
            action: Action name
            context: Action context
            user_roles: Roles of the user/agent
            
        Returns:
            Matching ApprovalRule if approval needed, None otherwise
        """
        user_roles = user_roles or set()
        
        for rule in self._rules:
            if not rule.requires_approval:
                continue
            
            if not rule.matches(action, context):
                continue
            
            # Check for bypass
            if rule.bypass_roles & user_roles:
                logger.debug(f"Bypassing approval for {action} (user has bypass role)")
                continue
            
            return rule
        
        return None
    
    async def request_approval(
        self,
        run_id: str,
        action: str,
        context: Dict[str, Any],
        rule: Optional[ApprovalRule] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Request approval for an action.
        
        Args:
            run_id: Workflow run ID
            action: Action name
            context: Action context
            rule: Specific rule (or find matching)
            metadata: Additional metadata
            
        Returns:
            True if approved, False if denied/timeout
        """
        # Find matching rule if not provided
        if rule is None:
            rule = await self.check(action, context)
            if rule is None:
                # No approval needed
                return True
        
        now = datetime.utcnow()
        request_id = str(uuid4())
        
        request = ApprovalRequest(
            id=request_id,
            run_id=run_id,
            action=action,
            context=context,
            rule_name=rule.name,
            risk_level=rule.risk_level,
            status=ApprovalStatus.PENDING,
            created_at=now,
            timeout_at=now + timedelta(seconds=rule.timeout_seconds)
        )
        
        self._pending[request_id] = request
        self._approval_waiters[request_id] = asyncio.Event()
        
        # Notify handlers
        for handler in self._on_request_handlers:
            try:
                handler(request)
            except Exception as e:
                logger.warning(f"Approval request handler error: {e}")
        
        logger.info(
            f"Approval requested: {action} (run={run_id}, risk={rule.risk_level.value})"
        )
        
        # Wait for response or timeout
        try:
            await asyncio.wait_for(
                self._approval_waiters[request_id].wait(),
                timeout=rule.timeout_seconds
            )
            
            result = self._approval_results.get(request_id, False)
            
        except asyncio.TimeoutError:
            # Handle timeout
            if rule.auto_approve_after:
                # Auto-approve
                request.status = ApprovalStatus.AUTO_APPROVED
                request.resolved_at = datetime.utcnow()
                request.resolution_reason = "Auto-approved after timeout"
                result = True
                logger.info(f"Auto-approved {action} after timeout")
            
            elif rule.escalate_to:
                # Escalate
                request.status = ApprovalStatus.ESCALATED
                request.escalation_chain.append(rule.escalate_to)
                # In production, this would trigger escalation notification
                logger.warning(f"Escalating {action} to {rule.escalate_to}")
                result = False
            
            else:
                request.status = ApprovalStatus.TIMEOUT
                request.resolved_at = datetime.utcnow()
                result = False
                logger.warning(f"Approval timeout for {action}")
        
        finally:
            # Cleanup
            if request_id in self._pending:
                del self._pending[request_id]
            if request_id in self._approval_waiters:
                del self._approval_waiters[request_id]
            if request_id in self._approval_results:
                del self._approval_results[request_id]
            
            # Store in history
            self._history.append(request)
        
        # Notify response handlers
        for handler in self._on_response_handlers:
            try:
                handler(request)
            except Exception as e:
                logger.warning(f"Approval response handler error: {e}")
        
        return result
    
    async def approve(
        self,
        request_id: str,
        approver: str,
        reason: Optional[str] = None
    ):
        """
        Approve a pending request.
        
        Args:
            request_id: Approval request ID
            approver: Who is approving
            reason: Optional reason
        """
        if request_id not in self._pending:
            logger.warning(f"Approval request {request_id} not found")
            return
        
        request = self._pending[request_id]
        request.status = ApprovalStatus.APPROVED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = approver
        request.resolution_reason = reason
        
        self._approval_results[request_id] = True
        
        if request_id in self._approval_waiters:
            self._approval_waiters[request_id].set()
        
        logger.info(f"Approved: {request.action} by {approver}")
    
    async def deny(
        self,
        request_id: str,
        denier: str,
        reason: Optional[str] = None
    ):
        """
        Deny a pending request.
        
        Args:
            request_id: Approval request ID
            denier: Who is denying
            reason: Optional reason
        """
        if request_id not in self._pending:
            logger.warning(f"Approval request {request_id} not found")
            return
        
        request = self._pending[request_id]
        request.status = ApprovalStatus.DENIED
        request.resolved_at = datetime.utcnow()
        request.resolved_by = denier
        request.resolution_reason = reason
        
        self._approval_results[request_id] = False
        
        if request_id in self._approval_waiters:
            self._approval_waiters[request_id].set()
        
        logger.info(f"Denied: {request.action} by {denier} - {reason}")
    
    def get_pending(self, run_id: Optional[str] = None) -> List[ApprovalRequest]:
        """Get pending approval requests"""
        if run_id:
            return [r for r in self._pending.values() if r.run_id == run_id]
        return list(self._pending.values())
    
    def get_history(
        self,
        run_id: Optional[str] = None,
        status: Optional[ApprovalStatus] = None,
        limit: int = 100
    ) -> List[ApprovalRequest]:
        """Get approval history"""
        history = self._history.copy()
        
        if run_id:
            history = [r for r in history if r.run_id == run_id]
        if status:
            history = [r for r in history if r.status == status]
        
        return sorted(history, key=lambda r: r.created_at, reverse=True)[:limit]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get approval statistics"""
        total = len(self._history)
        
        if total == 0:
            return {
                "total": 0,
                "approved": 0,
                "denied": 0,
                "timeout": 0,
                "auto_approved": 0,
                "approval_rate": 0,
                "avg_response_time_ms": 0
            }
        
        approved = len([r for r in self._history if r.status == ApprovalStatus.APPROVED])
        denied = len([r for r in self._history if r.status == ApprovalStatus.DENIED])
        timeout = len([r for r in self._history if r.status == ApprovalStatus.TIMEOUT])
        auto = len([r for r in self._history if r.status == ApprovalStatus.AUTO_APPROVED])
        
        # Calculate average response time
        response_times = []
        for r in self._history:
            if r.resolved_at and r.status in [ApprovalStatus.APPROVED, ApprovalStatus.DENIED]:
                rt = (r.resolved_at - r.created_at).total_seconds() * 1000
                response_times.append(rt)
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "total": total,
            "pending": len(self._pending),
            "approved": approved,
            "denied": denied,
            "timeout": timeout,
            "auto_approved": auto,
            "approval_rate": (approved + auto) / total * 100,
            "avg_response_time_ms": avg_response,
            "by_risk_level": {
                level.value: len([r for r in self._history if r.risk_level == level])
                for level in RiskLevel
            }
        }


# Workflow integration mixin
class ApprovalMixin:
    """
    Mixin for workflow classes to enable approval gating.
    
    Usage:
        class MyWorkflow(ApprovalMixin):
            async def run(self, input):
                # Check if approval needed
                if await self.needs_approval("send_email", {"to": "..."}):
                    approved = await self.get_approval("send_email", {"to": "..."})
                    if not approved:
                        raise PermissionError("Action denied")
                
                # Proceed with action
                await self.send_email(...)
    """
    
    _approval_gate: Optional[ApprovalGate] = None
    _run_id: Optional[str] = None
    _user_roles: Set[str] = field(default_factory=set)
    
    def setup_approval(
        self,
        gate: Optional[ApprovalGate] = None,
        run_id: Optional[str] = None,
        user_roles: Optional[Set[str]] = None
    ):
        """Setup approval for this workflow instance"""
        self._approval_gate = gate or get_approval_gate()
        self._run_id = run_id
        self._user_roles = user_roles or set()
    
    async def needs_approval(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """Check if an action needs approval"""
        if not self._approval_gate:
            return False
        
        rule = await self._approval_gate.check(action, context, self._user_roles)
        return rule is not None
    
    async def get_approval(
        self,
        action: str,
        context: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> bool:
        """
        Request approval for an action.
        
        Returns True if approved, False if denied/timeout.
        """
        if not self._approval_gate or not self._run_id:
            return True  # Auto-approve if not configured
        
        rule = await self._approval_gate.check(action, context, self._user_roles)
        if rule is None:
            return True  # No approval needed
        
        # Optionally override timeout
        if timeout:
            rule = ApprovalRule(
                name=rule.name,
                pattern=rule.pattern,
                requires_approval=True,
                risk_level=rule.risk_level,
                timeout_seconds=timeout
            )
        
        return await self._approval_gate.request_approval(
            self._run_id, action, context, rule
        )


# Singleton gate instance
_gate: Optional[ApprovalGate] = None

def get_approval_gate() -> ApprovalGate:
    """Get the global approval gate instance"""
    global _gate
    if _gate is None:
        _gate = ApprovalGate()
    return _gate


# FastAPI endpoints for approval management
try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/approvals", tags=["approvals"])
    
    class ApprovalResponse(BaseModel):
        approved: bool
        reason: Optional[str] = None
    
    @router.get("/pending")
    async def list_pending(run_id: Optional[str] = None):
        """List pending approval requests"""
        gate = get_approval_gate()
        pending = gate.get_pending(run_id)
        return {
            "pending": [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "action": r.action,
                    "context": r.context,
                    "risk_level": r.risk_level.value,
                    "created_at": r.created_at.isoformat(),
                    "timeout_at": r.timeout_at.isoformat()
                }
                for r in pending
            ]
        }
    
    @router.post("/{request_id}/approve")
    async def approve_request(
        request_id: str,
        approver: str = "api",
        reason: Optional[str] = None
    ):
        """Approve a pending request"""
        gate = get_approval_gate()
        await gate.approve(request_id, approver, reason)
        return {"status": "approved"}
    
    @router.post("/{request_id}/deny")
    async def deny_request(
        request_id: str,
        denier: str = "api",
        reason: Optional[str] = None
    ):
        """Deny a pending request"""
        gate = get_approval_gate()
        await gate.deny(request_id, denier, reason)
        return {"status": "denied"}
    
    @router.get("/history")
    async def get_history(
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ):
        """Get approval history"""
        gate = get_approval_gate()
        status_enum = ApprovalStatus(status) if status else None
        history = gate.get_history(run_id, status_enum, limit)
        return {
            "history": [
                {
                    "id": r.id,
                    "run_id": r.run_id,
                    "action": r.action,
                    "status": r.status.value,
                    "risk_level": r.risk_level.value,
                    "created_at": r.created_at.isoformat(),
                    "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
                    "resolved_by": r.resolved_by,
                    "resolution_reason": r.resolution_reason
                }
                for r in history
            ]
        }
    
    @router.get("/stats")
    async def get_stats():
        """Get approval statistics"""
        gate = get_approval_gate()
        return gate.get_stats()
    
    @router.get("/rules")
    async def list_rules():
        """List approval rules"""
        gate = get_approval_gate()
        return {
            "rules": [
                {
                    "name": r.name,
                    "pattern": r.pattern,
                    "risk_level": r.risk_level.value,
                    "timeout_seconds": r.timeout_seconds,
                    "auto_approve_after": r.auto_approve_after
                }
                for r in gate.get_rules()
            ]
        }

except ImportError:
    router = None


# Export
__all__ = [
    "ApprovalGate",
    "ApprovalRule",
    "ApprovalRequest",
    "ApprovalStatus",
    "RiskLevel",
    "ApprovalMixin",
    "get_approval_gate",
    "router"
]
