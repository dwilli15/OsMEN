#!/usr/bin/env python3
"""
Embedding Optimization for OsMEN

Provides multiple embedding backends with performance comparison:
- all-MiniLM-L6-v2: Fast, good quality (384 dims)
- BAAI/bge-small-en-v1.5: Better quality (384 dims)
- BAAI/bge-base-en-v1.5: Best quality (768 dims)
- nomic-ai/nomic-embed-text-v1.5: Great for RAG (768 dims)

Features:
- Automatic model selection based on use case
- Batch processing for efficiency
- Caching for repeated embeddings
- ChromaDB integration
"""

import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check dependencies
try:
    from sentence_transformers import SentenceTransformer

    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not available")

try:
    import torch

    TORCH_AVAILABLE = True
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    TORCH_AVAILABLE = False
    CUDA_AVAILABLE = False


@dataclass
class EmbeddingModel:
    """Configuration for an embedding model"""

    name: str
    model_id: str
    dimensions: int
    description: str
    quality_score: float  # 0-1, higher is better
    speed_score: float  # 0-1, higher is faster
    use_cases: List[str]


# Available embedding models
EMBEDDING_MODELS = {
    "minilm": EmbeddingModel(
        name="minilm",
        model_id="all-MiniLM-L6-v2",
        dimensions=384,
        description="Fast and lightweight, good for general use",
        quality_score=0.7,
        speed_score=0.95,
        use_cases=["general", "chat", "fast-search"],
    ),
    "bge-small": EmbeddingModel(
        name="bge-small",
        model_id="BAAI/bge-small-en-v1.5",
        dimensions=384,
        description="Small but high quality, optimized for retrieval",
        quality_score=0.85,
        speed_score=0.9,
        use_cases=["rag", "retrieval", "semantic-search"],
    ),
    "bge-base": EmbeddingModel(
        name="bge-base",
        model_id="BAAI/bge-base-en-v1.5",
        dimensions=768,
        description="High quality, best for important retrieval tasks",
        quality_score=0.92,
        speed_score=0.7,
        use_cases=["rag", "document-retrieval", "knowledge-base"],
    ),
    "nomic": EmbeddingModel(
        name="nomic",
        model_id="nomic-ai/nomic-embed-text-v1.5",
        dimensions=768,
        description="Excellent for RAG, long context support",
        quality_score=0.9,
        speed_score=0.75,
        use_cases=["rag", "long-documents", "research"],
    ),
    "e5-small": EmbeddingModel(
        name="e5-small",
        model_id="intfloat/e5-small-v2",
        dimensions=384,
        description="Efficient E5 model for general embedding",
        quality_score=0.82,
        speed_score=0.88,
        use_cases=["general", "retrieval", "classification"],
    ),
}


class EmbeddingCache:
    """Simple file-based embedding cache"""

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "osmen" / "embeddings"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, List[float]] = {}

    def _get_key(self, text: str, model: str) -> str:
        """Generate cache key"""
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = self._get_key(text, model)

        # Check memory cache
        if key in self._memory_cache:
            return self._memory_cache[key]

        # Check file cache
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    data = json.load(f)
                    self._memory_cache[key] = data["embedding"]
                    return data["embedding"]
            except:
                pass

        return None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """Cache an embedding"""
        key = self._get_key(text, model)
        self._memory_cache[key] = embedding

        # Also save to file
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, "w") as f:
                json.dump({"model": model, "embedding": embedding}, f)
        except:
            pass

    def clear(self) -> int:
        """Clear all cached embeddings"""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
            count += 1
        self._memory_cache.clear()
        return count


class EmbeddingProvider:
    """
    Unified embedding provider for OsMEN.

    Supports multiple models with automatic selection based on use case.
    Includes caching and batch processing for efficiency.
    """

    def __init__(
        self,
        model_name: str = "minilm",
        use_cache: bool = True,
        device: str = "auto",
    ):
        self.model_config = EMBEDDING_MODELS.get(model_name, EMBEDDING_MODELS["minilm"])
        self._model = None
        self.use_cache = use_cache
        self.cache = EmbeddingCache() if use_cache else None

        # Determine device
        if device == "auto":
            self.device = "cuda" if CUDA_AVAILABLE else "cpu"
        else:
            self.device = device

        logger.info(
            f"Embedding provider: {self.model_config.model_id} on {self.device}"
        )

    @property
    def model(self):
        """Lazy-load embedding model"""
        if self._model is None and ST_AVAILABLE:
            logger.info(f"Loading model: {self.model_config.model_id}")
            self._model = SentenceTransformer(
                self.model_config.model_id,
                device=self.device,
            )
        return self._model

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.model_config.dimensions

    def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        # Check cache
        if self.cache:
            cached = self.cache.get(text, self.model_config.model_id)
            if cached:
                return cached

        # Generate embedding
        if not self.model:
            raise RuntimeError("Embedding model not available")

        embedding = self.model.encode(text, convert_to_numpy=True).tolist()

        # Cache result
        if self.cache:
            self.cache.set(text, self.model_config.model_id, embedding)

        return embedding

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts efficiently"""
        if not self.model:
            raise RuntimeError("Embedding model not available")

        # Check cache for each text
        results = [None] * len(texts)
        uncached_indices = []
        uncached_texts = []

        if self.cache:
            for i, text in enumerate(texts):
                cached = self.cache.get(text, self.model_config.model_id)
                if cached:
                    results[i] = cached
                else:
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(texts)))
            uncached_texts = texts

        # Generate embeddings for uncached texts
        if uncached_texts:
            embeddings = self.model.encode(
                uncached_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
            )

            for i, idx in enumerate(uncached_indices):
                emb = embeddings[i].tolist()
                results[idx] = emb
                if self.cache:
                    self.cache.set(texts[idx], self.model_config.model_id, emb)

        return results

    def similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts"""
        emb1 = self.embed(text1)
        emb2 = self.embed(text2)

        # Cosine similarity
        dot = sum(a * b for a, b in zip(emb1, emb2))
        norm1 = sum(a * a for a in emb1) ** 0.5
        norm2 = sum(b * b for b in emb2) ** 0.5

        return dot / (norm1 * norm2) if norm1 and norm2 else 0

    @staticmethod
    def recommend_model(use_case: str) -> str:
        """Recommend a model based on use case"""
        use_case = use_case.lower()

        best_match = "minilm"
        best_score = 0

        for name, config in EMBEDDING_MODELS.items():
            for uc in config.use_cases:
                if use_case in uc or uc in use_case:
                    score = config.quality_score
                    if score > best_score:
                        best_score = score
                        best_match = name

        return best_match


class ChromaDBEmbeddingFunction:
    """
    Custom embedding function for ChromaDB.

    Use this when creating ChromaDB collections:

    ```python
    from integrations.embedding_optimizer import ChromaDBEmbeddingFunction

    ef = ChromaDBEmbeddingFunction(model_name="bge-small")
    collection = client.create_collection(
        name="my_collection",
        embedding_function=ef,
    )
    ```
    """

    def __init__(self, model_name: str = "bge-small"):
        self.provider = EmbeddingProvider(model_name=model_name)

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Generate embeddings for ChromaDB"""
        return self.provider.embed_batch(input)


def benchmark_models(test_texts: List[str] = None) -> Dict[str, Any]:
    """Benchmark available embedding models"""
    if not ST_AVAILABLE:
        return {"error": "sentence-transformers not available"}

    test_texts = test_texts or [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "ChromaDB is a vector database for AI applications.",
        "Python is a versatile programming language.",
        "Natural language processing enables computers to understand text.",
    ]

    results = {}

    for name, config in EMBEDDING_MODELS.items():
        try:
            logger.info(f"Benchmarking: {name}")

            # Time model loading
            load_start = time.time()
            provider = EmbeddingProvider(model_name=name, use_cache=False)
            _ = provider.model  # Force load
            load_time = time.time() - load_start

            # Time embedding generation
            embed_start = time.time()
            embeddings = provider.embed_batch(test_texts)
            embed_time = time.time() - embed_start

            results[name] = {
                "model_id": config.model_id,
                "dimensions": config.dimensions,
                "load_time_s": round(load_time, 3),
                "embed_time_s": round(embed_time, 3),
                "texts_per_second": round(len(test_texts) / embed_time, 1),
                "quality_score": config.quality_score,
                "status": "ok",
            }

        except Exception as e:
            results[name] = {
                "model_id": config.model_id,
                "status": "error",
                "error": str(e),
            }

    return results


def main():
    """CLI for embedding optimization"""
    import argparse

    parser = argparse.ArgumentParser(description="Embedding Optimizer for OsMEN")
    parser.add_argument(
        "--model", default="minilm", choices=list(EMBEDDING_MODELS.keys())
    )
    parser.add_argument("--benchmark", action="store_true", help="Benchmark all models")
    parser.add_argument("--embed", help="Text to embed")
    parser.add_argument(
        "--similarity", nargs=2, help="Calculate similarity between two texts"
    )
    parser.add_argument("--recommend", help="Recommend model for use case")
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear embedding cache"
    )

    args = parser.parse_args()

    if args.benchmark:
        print("Benchmarking embedding models...")
        results = benchmark_models()
        print(json.dumps(results, indent=2))

    elif args.embed:
        provider = EmbeddingProvider(model_name=args.model)
        embedding = provider.embed(args.embed)
        print(f"Model: {provider.model_config.model_id}")
        print(f"Dimensions: {len(embedding)}")
        print(f"Embedding (first 10): {embedding[:10]}")

    elif args.similarity:
        provider = EmbeddingProvider(model_name=args.model)
        sim = provider.similarity(args.similarity[0], args.similarity[1])
        print(f"Similarity: {sim:.4f}")

    elif args.recommend:
        model = EmbeddingProvider.recommend_model(args.recommend)
        config = EMBEDDING_MODELS[model]
        print(f"Recommended model: {model}")
        print(f"  Model ID: {config.model_id}")
        print(f"  Dimensions: {config.dimensions}")
        print(f"  Quality: {config.quality_score}")

    elif args.clear_cache:
        cache = EmbeddingCache()
        count = cache.clear()
        print(f"Cleared {count} cached embeddings")

    else:
        # Show available models
        print("Available Embedding Models:\n")
        for name, config in EMBEDDING_MODELS.items():
            print(f"  {name}:")
            print(f"    Model: {config.model_id}")
            print(f"    Dims: {config.dimensions}")
            print(f"    Quality: {config.quality_score:.0%}")
            print(f"    Speed: {config.speed_score:.0%}")
            print(f"    Use cases: {', '.join(config.use_cases)}")
            print()


if __name__ == "__main__":
    main()
