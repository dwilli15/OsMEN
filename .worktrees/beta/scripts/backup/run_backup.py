#!/usr/bin/env python3
"""Create database and file backups for OsMEN."""

import argparse
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "./backups"))


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_pg_dump(target: Path) -> None:
    env = os.environ.copy()
    user = env.get("OSMEN_DB_USER", env.get("POSTGRES_USER", "postgres"))
    password = env.get("OSMEN_DB_PASSWORD", env.get("POSTGRES_PASSWORD", "postgres"))
    host = env.get("OSMEN_DB_HOST", "postgres")
    port = env.get("OSMEN_DB_PORT", "5432")
    name = env.get("OSMEN_DB_NAME", "osmen_app")
    env["PGPASSWORD"] = password
    cmd = [
        "pg_dump",
        f"--host={host}",
        f"--port={port}",
        f"--username={user}",
        "--format=custom",
        f"--file={target}",
        name,
    ]
    subprocess.run(cmd, check=True, env=env)


def snapshot_qdrant(target: Path) -> None:
    src = Path("qdrant_data/snapshots")
    if src.exists():
        shutil.make_archive(str(target), "zip", src)


def backup_content(target: Path) -> None:
    content_dir = Path("content")
    if content_dir.exists():
        shutil.make_archive(str(target), "zip", content_dir)


def main():
    parser = argparse.ArgumentParser(description="Run OsMEN backup")
    parser.add_argument("--label", default=None)
    args = parser.parse_args()

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    label = args.label or "manual"
    dest = ensure_dir(BACKUP_DIR / label / timestamp)

    run_pg_dump(dest / "postgres.dump")
    snapshot_qdrant(dest / "qdrant")
    backup_content(dest / "content")
    print(f"Backups written to {dest}")


if __name__ == "__main__":
    main()
