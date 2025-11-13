#!/usr/bin/env python3
"""Apply database migrations stored in database/migrations."""

import asyncio
from pathlib import Path

from database.connection import get_pool

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "database" / "migrations"


async def apply_migrations():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )

        rows = await conn.fetch("SELECT version FROM schema_migrations")
        applied = {row[0] for row in rows}

        migrations = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for path in migrations:
            version = path.stem
            if version in applied:
                continue
            sql = path.read_text()
            await conn.execute(sql)
            await conn.execute(
                "INSERT INTO schema_migrations(version) VALUES($1)", version
            )
            print(f"Applied migration {version}")


if __name__ == "__main__":
    asyncio.run(apply_migrations())
