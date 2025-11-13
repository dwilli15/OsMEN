from __future__ import annotations

import json
from typing import Any, Dict, Optional

from database.connection import get_pool


async def record_audit(actor: str, action: str, context: Optional[Dict[str, Any]] = None) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO audit_logs(actor, action, context) VALUES($1, $2, $3)",
            actor,
            action,
            json.dumps(context or {}),
        )
