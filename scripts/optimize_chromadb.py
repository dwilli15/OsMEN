#!/usr/bin/env python3
"""
ChromaDB Optimization for OsMEN

Configures ChromaDB collections with optimized HNSW parameters for:
- Better recall (finding more relevant results)
- Faster search (optimized index building)
- GPU acceleration (if available)

Collections:
- obsidian_vault: Knowledge base from Obsidian
- librarian_docs: RAG document storage
- agent_memory: Agent conversation/context memory
- research_intel: Research and web scraping results
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.error("ChromaDB not installed. Run: pip install chromadb")


@dataclass
class CollectionConfig:
    """Configuration for a ChromaDB collection"""

    name: str
    description: str

    # HNSW parameters - higher values = better recall but slower indexing
    hnsw_space: str = "cosine"  # cosine, l2, ip (inner product)
    hnsw_construction_ef: int = 200  # Default 100, higher = better recall during build
    hnsw_search_ef: int = 150  # Default 10, higher = better recall during search
    hnsw_M: int = 32  # Default 16, connections per layer (higher = better recall)

    # Batch settings
    hnsw_batch_size: int = 100
    hnsw_sync_threshold: int = 1000


# Optimized collection configurations
COLLECTIONS = {
    "obsidian_vault": CollectionConfig(
        name="obsidian_vault",
        description="Knowledge base synced from Obsidian vault",
        hnsw_space="cosine",
        hnsw_construction_ef=200,
        hnsw_search_ef=150,
        hnsw_M=32,
    ),
    "librarian_docs": CollectionConfig(
        name="librarian_docs",
        description="RAG document storage for Librarian agent",
        hnsw_space="cosine",
        hnsw_construction_ef=256,  # Higher for document retrieval
        hnsw_search_ef=200,
        hnsw_M=48,  # More connections for diverse documents
    ),
    "agent_memory": CollectionConfig(
        name="agent_memory",
        description="Agent conversation and context memory",
        hnsw_space="cosine",
        hnsw_construction_ef=128,  # Lower for faster updates
        hnsw_search_ef=100,
        hnsw_M=24,
    ),
    "research_intel": CollectionConfig(
        name="research_intel",
        description="Research findings and web scraping results",
        hnsw_space="cosine",
        hnsw_construction_ef=200,
        hnsw_search_ef=150,
        hnsw_M=32,
    ),
    "daily_notes": CollectionConfig(
        name="daily_notes",
        description="Daily notes with temporal context",
        hnsw_space="cosine",
        hnsw_construction_ef=128,
        hnsw_search_ef=100,
        hnsw_M=24,
    ),
}


class ChromaDBOptimizer:
    """Optimize ChromaDB collections for OsMEN"""

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        self._client = None

    @property
    def client(self):
        """Lazy-load ChromaDB client"""
        if self._client is None and CHROMA_AVAILABLE:
            try:
                self._client = chromadb.HttpClient(host=self.host, port=self.port)
                # Test connection
                self._client.heartbeat()
                logger.info(f"Connected to ChromaDB at {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"Failed to connect to ChromaDB: {e}")
                self._client = None
        return self._client

    def get_collection_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a collection"""
        if not self.client:
            return None

        try:
            collection = self.client.get_collection(name)
            return {
                "name": name,
                "count": collection.count(),
                "metadata": collection.metadata,
            }
        except Exception as e:
            return {"name": name, "error": str(e)}

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections with stats"""
        if not self.client:
            return []

        try:
            collections = self.client.list_collections()
            return [
                {
                    "name": c.name,
                    "count": c.count(),
                    "metadata": c.metadata,
                }
                for c in collections
            ]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []

    def create_optimized_collection(
        self,
        config: CollectionConfig,
        recreate: bool = False,
    ) -> Optional[Any]:
        """Create or update a collection with optimized settings"""
        if not self.client:
            return None

        try:
            # Check if exists
            existing = None
            try:
                existing = self.client.get_collection(config.name)
            except:
                pass

            if existing and recreate:
                logger.info(f"Deleting existing collection: {config.name}")
                self.client.delete_collection(config.name)
                existing = None
            elif existing:
                logger.info(
                    f"Collection exists: {config.name} ({existing.count()} items)"
                )
                return existing

            # Create with optimized metadata
            metadata = {
                "description": config.description,
                "hnsw:space": config.hnsw_space,
                "hnsw:construction_ef": config.hnsw_construction_ef,
                "hnsw:search_ef": config.hnsw_search_ef,
                "hnsw:M": config.hnsw_M,
                "hnsw:batch_size": config.hnsw_batch_size,
                "hnsw:sync_threshold": config.hnsw_sync_threshold,
            }

            collection = self.client.create_collection(
                name=config.name,
                metadata=metadata,
            )

            logger.info(f"Created optimized collection: {config.name}")
            logger.info(
                f"  HNSW params: M={config.hnsw_M}, ef_construction={config.hnsw_construction_ef}, ef_search={config.hnsw_search_ef}"
            )

            return collection

        except Exception as e:
            logger.error(f"Failed to create collection {config.name}: {e}")
            return None

    def setup_all_collections(self, recreate: bool = False) -> Dict[str, Any]:
        """Set up all OsMEN collections with optimized settings"""
        results = {
            "success": [],
            "failed": [],
            "skipped": [],
        }

        for name, config in COLLECTIONS.items():
            try:
                collection = self.create_optimized_collection(config, recreate=recreate)
                if collection:
                    results["success"].append(
                        {
                            "name": name,
                            "count": collection.count(),
                        }
                    )
                else:
                    results["failed"].append(name)
            except Exception as e:
                results["failed"].append({"name": name, "error": str(e)})

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get overall ChromaDB statistics"""
        if not self.client:
            return {"error": "Not connected"}

        try:
            collections = self.list_collections()
            total_items = sum(c.get("count", 0) for c in collections)

            return {
                "status": "connected",
                "host": f"{self.host}:{self.port}",
                "collections": len(collections),
                "total_items": total_items,
                "collection_details": collections,
            }
        except Exception as e:
            return {"error": str(e)}

    def optimize_existing_collection(self, name: str) -> Dict[str, Any]:
        """Optimize an existing collection by updating metadata"""
        if not self.client:
            return {"error": "Not connected"}

        if name not in COLLECTIONS:
            return {"error": f"Unknown collection: {name}"}

        config = COLLECTIONS[name]

        try:
            collection = self.client.get_collection(name)

            # Update metadata with optimized params
            # Note: Some params can only be set at creation time
            collection.modify(
                metadata={
                    "description": config.description,
                    "hnsw:search_ef": config.hnsw_search_ef,
                }
            )

            return {
                "success": True,
                "name": name,
                "count": collection.count(),
                "note": "Some HNSW params require recreation to take effect",
            }
        except Exception as e:
            return {"error": str(e)}


def main():
    """CLI for ChromaDB optimization"""
    import argparse

    parser = argparse.ArgumentParser(description="ChromaDB Optimizer for OsMEN")
    parser.add_argument("--host", default="localhost", help="ChromaDB host")
    parser.add_argument("--port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--setup", action="store_true", help="Set up all collections")
    parser.add_argument(
        "--recreate", action="store_true", help="Recreate existing collections"
    )
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--list", action="store_true", help="List collections")

    args = parser.parse_args()

    optimizer = ChromaDBOptimizer(host=args.host, port=args.port)

    if args.setup:
        print("Setting up optimized collections...")
        results = optimizer.setup_all_collections(recreate=args.recreate)
        print(json.dumps(results, indent=2))

    elif args.list:
        collections = optimizer.list_collections()
        print("\nCollections:")
        for c in collections:
            print(f"  - {c['name']}: {c['count']} items")

    elif args.stats:
        stats = optimizer.get_stats()
        print(json.dumps(stats, indent=2))

    else:
        # Default: show stats
        if optimizer.client:
            stats = optimizer.get_stats()
            print(f"\n📊 ChromaDB Stats")
            print(f"   Host: {stats.get('host', 'N/A')}")
            print(f"   Collections: {stats.get('collections', 0)}")
            print(f"   Total Items: {stats.get('total_items', 0)}")
            print("\nCollections:")
            for c in stats.get("collection_details", []):
                print(f"   - {c['name']}: {c['count']} items")
        else:
            print("❌ Could not connect to ChromaDB")
            print(f"   Tried: {args.host}:{args.port}")
            print("\n   Make sure Docker is running:")
            print("   docker-compose up -d chromadb")


if __name__ == "__main__":
    main()
