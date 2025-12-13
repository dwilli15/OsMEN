#!/usr/bin/env python3
"""
Enhanced RAG Pipeline for OsMEN

Features:
- Multi-stage retrieval (BM25 + semantic)
- Cross-encoder re-ranking
- Query expansion with LLM
- Hybrid scoring
- Result deduplication
- Context windowing

Use with Librarian, Obsidian, and Knowledge agents for improved retrieval.
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check dependencies
try:
    from sentence_transformers import CrossEncoder

    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False

try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank_bm25 not available. Install: pip install rank-bm25")


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline"""

    # Retrieval
    initial_k: int = 20  # Initial candidates to retrieve
    final_k: int = 5  # Final results after re-ranking

    # Weights for hybrid scoring
    semantic_weight: float = 0.6
    bm25_weight: float = 0.2
    rerank_weight: float = 0.2

    # Re-ranking
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    use_reranking: bool = True

    # Query expansion
    use_query_expansion: bool = False
    expansion_model: str = None  # LLM model for expansion

    # Deduplication
    dedupe_threshold: float = 0.9  # Similarity threshold for dedup

    # Context
    context_window: int = 3  # Sentences around match
    max_context_length: int = 1000


@dataclass
class RetrievalResult:
    """Single retrieval result"""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0
    semantic_score: float = 0.0
    bm25_score: float = 0.0
    rerank_score: float = 0.0
    source: str = ""


class BM25Retriever:
    """BM25 keyword-based retriever"""

    def __init__(self):
        self._index = None
        self._documents = []
        self._doc_ids = []

    def index(self, documents: List[Dict[str, Any]]) -> None:
        """Index documents for BM25 search"""
        if not BM25_AVAILABLE:
            return

        self._documents = documents
        self._doc_ids = [d.get("id", str(i)) for i, d in enumerate(documents)]

        # Tokenize documents
        tokenized = [self._tokenize(d.get("content", "")) for d in documents]
        self._index = BM25Okapi(tokenized)

        logger.info(f"Indexed {len(documents)} documents for BM25")

    def search(self, query: str, k: int = 10) -> List[Tuple[str, float]]:
        """Search with BM25"""
        if not self._index or not BM25_AVAILABLE:
            return []

        tokens = self._tokenize(query)
        scores = self._index.get_scores(tokens)

        # Get top-k
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :k
        ]

        return [(self._doc_ids[i], scores[i]) for i in top_indices]

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple tokenization"""
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r"\b\w+\b", text.lower())
        return tokens


class CrossEncoderReranker:
    """Cross-encoder for re-ranking results"""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self):
        """Lazy-load cross-encoder"""
        if self._model is None and CROSS_ENCODER_AVAILABLE:
            logger.info(f"Loading cross-encoder: {self.model_name}")
            self._model = CrossEncoder(self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
    ) -> List[RetrievalResult]:
        """Re-rank results using cross-encoder"""
        if not self.model or not results:
            return results

        # Prepare pairs
        pairs = [(query, r.content) for r in results]

        # Get scores
        scores = self.model.predict(pairs)

        # Update results with rerank scores
        for i, result in enumerate(results):
            result.rerank_score = float(scores[i])

        # Sort by rerank score
        return sorted(results, key=lambda x: x.rerank_score, reverse=True)


class QueryExpander:
    """Expand queries using LLM or rules"""

    def __init__(self, llm_fn: Optional[Callable[[str], str]] = None):
        self.llm_fn = llm_fn

    def expand(self, query: str) -> List[str]:
        """Expand query into multiple variations"""
        expansions = [query]

        # Rule-based expansions
        expansions.extend(self._rule_based_expand(query))

        # LLM-based expansion
        if self.llm_fn:
            try:
                llm_expansion = self.llm_fn(
                    f"Generate 3 alternative search queries for: {query}\n"
                    "Return only the queries, one per line."
                )
                expansions.extend(llm_expansion.strip().split("\n"))
            except Exception as e:
                logger.warning(f"LLM expansion failed: {e}")

        return list(set(expansions))[:5]  # Dedupe and limit

    @staticmethod
    def _rule_based_expand(query: str) -> List[str]:
        """Simple rule-based query expansion"""
        expansions = []

        # Add question form
        if not query.endswith("?"):
            expansions.append(f"What is {query}?")
            expansions.append(f"How to {query}?")

        # Remove common words
        common = {"the", "a", "an", "is", "are", "was", "were", "to", "of", "and", "or"}
        words = query.lower().split()
        filtered = " ".join(w for w in words if w not in common)
        if filtered != query.lower():
            expansions.append(filtered)

        return expansions


class EnhancedRAGPipeline:
    """
    Enhanced RAG pipeline with multi-stage retrieval.

    Stages:
    1. Query expansion (optional)
    2. Semantic search (vector similarity)
    3. BM25 keyword search
    4. Hybrid scoring
    5. Cross-encoder re-ranking
    6. Deduplication
    7. Context windowing
    """

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        embedding_fn: Optional[Callable[[str], List[float]]] = None,
        search_fn: Optional[Callable[[str, int], List[Dict]]] = None,
        llm_fn: Optional[Callable[[str], str]] = None,
    ):
        self.config = config or RAGConfig()
        self.embedding_fn = embedding_fn
        self.search_fn = search_fn  # Semantic search function

        # Components
        self.bm25 = BM25Retriever()
        self.reranker = (
            CrossEncoderReranker(self.config.rerank_model)
            if self.config.use_reranking
            else None
        )
        self.expander = (
            QueryExpander(llm_fn) if self.config.use_query_expansion else None
        )

        # Document store for BM25
        self._documents: Dict[str, Dict] = {}

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Index documents for BM25 search"""
        for doc in documents:
            doc_id = doc.get(
                "id", hashlib.md5(doc.get("content", "").encode()).hexdigest()[:12]
            )
            self._documents[doc_id] = doc

        self.bm25.index(documents)

    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Execute full RAG retrieval pipeline.

        Refactored from complexity 29 to ~10 (PHOENIX Protocol compliance).

        Args:
            query: Search query
            k: Number of results (default: config.final_k)

        Returns:
            List of RetrievalResult objects
        """
        k = k or self.config.final_k
        initial_k = self.config.initial_k

        # Stage 1: Query expansion
        queries = self._expand_queries(query)

        # Stage 2: Semantic search
        semantic_results = self._semantic_search(queries, initial_k)

        # Stage 3: BM25 search
        bm25_scores = self._bm25_search(queries, initial_k)

        # Stage 4: Hybrid scoring
        results = self._hybrid_scoring(semantic_results, bm25_scores, initial_k)

        # Stage 5: Re-ranking
        results = self._apply_reranking(query, results)

        # Stage 6: Deduplication
        results = self._deduplicate(results)

        # Stage 7: Context windowing
        for r in results:
            r.content = self._extract_context(r.content, query)

        return results[:k]

    def _expand_queries(self, query: str) -> List[str]:
        """Stage 1: Expand query into multiple queries."""
        queries = [query]
        if self.expander:
            queries = self.expander.expand(query)
            logger.debug(f"Expanded to {len(queries)} queries")
        return queries

    def _semantic_search(
        self, queries: List[str], initial_k: int
    ) -> List[RetrievalResult]:
        """Stage 2: Execute semantic search across all queries."""
        semantic_results = []
        if self.search_fn:
            for q in queries:
                results = self.search_fn(q, initial_k)
                for r in results:
                    result = RetrievalResult(
                        id=r.get("id", ""),
                        content=r.get("content", ""),
                        metadata=r.get("metadata", {}),
                        semantic_score=r.get("score", 0),
                        source="semantic",
                    )
                    semantic_results.append(result)
        return semantic_results

    def _bm25_search(self, queries: List[str], initial_k: int) -> Dict[str, float]:
        """Stage 3: Execute BM25 search if available."""
        bm25_scores: Dict[str, float] = {}
        if BM25_AVAILABLE and self._documents:
            for q in queries:
                for doc_id, score in self.bm25.search(q, initial_k):
                    if doc_id in bm25_scores:
                        bm25_scores[doc_id] = max(bm25_scores[doc_id], score)
                    else:
                        bm25_scores[doc_id] = score
        return bm25_scores

    def _hybrid_scoring(
        self,
        semantic_results: List[RetrievalResult],
        bm25_scores: Dict[str, float],
        initial_k: int,
    ) -> List[RetrievalResult]:
        """Stage 4: Combine semantic and BM25 scores."""
        results_map: Dict[str, RetrievalResult] = {}

        # Add semantic results
        for r in semantic_results:
            if r.id not in results_map:
                results_map[r.id] = r
            else:
                if r.semantic_score > results_map[r.id].semantic_score:
                    results_map[r.id].semantic_score = r.semantic_score

        # Add BM25 scores
        for doc_id, score in bm25_scores.items():
            if doc_id in results_map:
                results_map[doc_id].bm25_score = score
            elif doc_id in self._documents:
                doc = self._documents[doc_id]
                results_map[doc_id] = RetrievalResult(
                    id=doc_id,
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                    bm25_score=score,
                    source="bm25",
                )

        # Calculate hybrid scores
        results = list(results_map.values())
        max_semantic = max((r.semantic_score for r in results), default=1) or 1
        max_bm25 = max((r.bm25_score for r in results), default=1) or 1

        for r in results:
            r.score = self.config.semantic_weight * (
                r.semantic_score / max_semantic
            ) + self.config.bm25_weight * (r.bm25_score / max_bm25)

        return sorted(results, key=lambda x: x.score, reverse=True)[:initial_k]

    def _apply_reranking(
        self, query: str, results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """Stage 5: Apply re-ranking if enabled."""
        if not (
            self.reranker and self.config.use_reranking and CROSS_ENCODER_AVAILABLE
        ):
            return results

        results = self.reranker.rerank(query, results)

        # Update final scores with rerank
        max_rerank = max((r.rerank_score for r in results), default=1) or 1
        for r in results:
            r.score = (
                1 - self.config.rerank_weight
            ) * r.score + self.config.rerank_weight * (r.rerank_score / max_rerank)

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _deduplicate(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Remove near-duplicate results"""
        if not results:
            return results

        unique = [results[0]]

        for r in results[1:]:
            is_dup = False
            for u in unique:
                # Simple overlap check
                r_words = set(r.content.lower().split())
                u_words = set(u.content.lower().split())
                overlap = len(r_words & u_words) / max(len(r_words | u_words), 1)

                if overlap > self.config.dedupe_threshold:
                    is_dup = True
                    break

            if not is_dup:
                unique.append(r)

        return unique

    def _extract_context(self, content: str, query: str) -> str:
        """Extract relevant context around query matches"""
        if len(content) <= self.config.max_context_length:
            return content

        # Find query terms in content
        query_terms = set(query.lower().split())
        sentences = re.split(r"[.!?]+", content)

        # Score sentences by query term overlap
        scored = []
        for i, sent in enumerate(sentences):
            sent_terms = set(sent.lower().split())
            overlap = len(query_terms & sent_terms)
            scored.append((i, overlap, sent))

        # Get best matching sentences with context
        scored = sorted(scored, key=lambda x: x[1], reverse=True)

        selected_indices = set()
        for idx, _, _ in scored[:3]:
            # Add surrounding sentences
            for i in range(
                max(0, idx - self.config.context_window),
                min(len(sentences), idx + self.config.context_window + 1),
            ):
                selected_indices.add(i)

        # Build context
        context_sents = [sentences[i] for i in sorted(selected_indices)]
        context = ". ".join(context_sents)

        if len(context) > self.config.max_context_length:
            context = context[: self.config.max_context_length] + "..."

        return context


# Convenience function for ChromaDB integration
def create_chromadb_rag_pipeline(
    chroma_client,
    collection_name: str,
    config: Optional[RAGConfig] = None,
) -> EnhancedRAGPipeline:
    """
    Create RAG pipeline with ChromaDB backend.

    Usage:
    ```python
    import chromadb
    from integrations.rag_pipeline import create_chromadb_rag_pipeline

    client = chromadb.HttpClient()
    pipeline = create_chromadb_rag_pipeline(client, "obsidian_vault")

    results = pipeline.retrieve("algorithm complexity")
    for r in results:
        print(f"{r.content[:100]}... (score: {r.score:.3f})")
    ```
    """
    collection = chroma_client.get_collection(collection_name)

    def search_fn(query: str, k: int) -> List[Dict]:
        results = collection.query(query_texts=[query], n_results=k)

        formatted = []
        for i, doc in enumerate(results["documents"][0]):
            formatted.append(
                {
                    "id": results["ids"][0][i],
                    "content": doc,
                    "metadata": (
                        results["metadatas"][0][i] if results["metadatas"] else {}
                    ),
                    "score": 1
                    - (results["distances"][0][i] if results["distances"] else 0),
                }
            )

        return formatted

    pipeline = EnhancedRAGPipeline(
        config=config,
        search_fn=search_fn,
    )

    return pipeline


def main():
    """Test RAG pipeline"""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced RAG Pipeline")
    parser.add_argument("--query", help="Test query")
    parser.add_argument(
        "--collection", default="obsidian_vault", help="ChromaDB collection"
    )

    args = parser.parse_args()

    if args.query:
        try:
            import chromadb

            client = chromadb.HttpClient(host="localhost", port=8000)

            pipeline = create_chromadb_rag_pipeline(client, args.collection)
            results = pipeline.retrieve(args.query)

            print(f"\nResults for: {args.query}\n")
            for i, r in enumerate(results):
                print(f"{i+1}. [{r.score:.3f}] {r.content[:100]}...")
                print(f"   Source: {r.metadata.get('title', 'Unknown')}")
                print()
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("Enhanced RAG Pipeline")
        print("=" * 40)
        print(f"BM25 available: {BM25_AVAILABLE}")
        print(f"Cross-encoder available: {CROSS_ENCODER_AVAILABLE}")
        print()
        print("Usage: python rag_pipeline.py --query 'your search query'")


if __name__ == "__main__":
    main()
