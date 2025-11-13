#!/usr/bin/env python3
"""Ensure required Qdrant collections exist."""

import argparse
import json
from pathlib import Path

from qdrant_client import QdrantClient

CONFIG_PATH = Path(__file__).resolve().parents[2] / "qdrant" / "config" / "collections.json"


def parse_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("collections", [])


def ensure_collections(host: str, api_key: str | None, dry_run: bool = False):
    client = QdrantClient(host=host, api_key=api_key or None)
    existing = {c.name for c in client.get_collections().collections}

    for collection in parse_config():
        name = collection["name"]
        if name in existing:
            print(f"Collection {name} already exists")
            continue
        if dry_run:
            print(f"[dry-run] would create {name}")
            continue
        vectors = collection["vectors"]
        client.recreate_collection(
            collection_name=name,
            vectors_config={
                "size": vectors["size"],
                "distance": vectors["distance"],
            },
        )
        print(f"Created collection {name}")


def main():
    parser = argparse.ArgumentParser(description="Seed Qdrant collections")
    parser.add_argument("--host", default="http://localhost:6333")
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    ensure_collections(args.host, args.api_key, args.dry_run)


if __name__ == "__main__":
    main()
