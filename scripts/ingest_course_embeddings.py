#!/usr/bin/env python3
"""
Course RAG Embeddings Generator
Ingests course materials into ChromaDB for semantic search

Uses the Librarian agent infrastructure for:
- Syllabus content
- Extracted textbook chapters
- Course metadata
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

try:
    import chromadb
    from chromadb.config import Settings

    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False
    print("⚠️ chromadb not installed")


def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars

        # Try to break at sentence boundary
        if end < len(text):
            for sep in [". ", "! ", "? ", "\n\n", "\n"]:
                last_sep = text[start:end].rfind(sep)
                if last_sep > max_chars // 2:
                    end = start + last_sep + len(sep)
                    break

        chunk = text[start:end].strip()
        if len(chunk) > 100:  # Minimum chunk size
            chunks.append(chunk)

        start = end - overlap

    return chunks


def generate_doc_id(content: str, source: str, index: int = 0) -> str:
    """Generate unique document ID."""
    hash_input = f"{source}:{index}:{content[:200]}"
    return hashlib.md5(hash_input.encode()).hexdigest()


class CourseEmbeddings:
    """Manage course embeddings in ChromaDB."""

    def __init__(self, course_code: str, chroma_path: str = None):
        self.course_code = course_code
        self.collection_name = f"course_{course_code.lower()}"

        if not HAS_CHROMA:
            raise ImportError("chromadb required")

        # Connect to ChromaDB
        if chroma_path:
            self.client = chromadb.PersistentClient(path=chroma_path)
        else:
            self.client = chromadb.Client()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, metadata={"course": course_code}
        )

        print(f"✅ Connected to collection: {self.collection_name}")
        print(f"   Current documents: {self.collection.count()}")

    def add_document(self, content: str, source: str, metadata: Dict = None) -> int:
        """Add a document to the collection."""

        chunks = chunk_text(content)
        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            doc_id = generate_doc_id(chunk, source, i)

            meta = {
                "source": source,
                "course": self.course_code,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "timestamp": datetime.now().isoformat(),
            }
            if metadata:
                meta.update(metadata)

            ids.append(doc_id)
            documents.append(chunk)
            metadatas.append(meta)

        # Add to collection
        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)

        return len(chunks)

    def add_textbook(self, textbook_dir: Path) -> int:
        """Add all chapters from an extracted textbook."""

        metadata_file = textbook_dir / "metadata.json"
        if not metadata_file.exists():
            print(f"⚠️ No metadata found: {textbook_dir}")
            return 0

        with open(metadata_file) as f:
            book_meta = json.load(f)

        total_chunks = 0

        for chapter in book_meta.get("chapters", []):
            chapter_file = textbook_dir / chapter["text_file"]
            if not chapter_file.exists():
                continue

            content = chapter_file.read_text(encoding="utf-8")

            chunks = self.add_document(
                content=content,
                source=f"{book_meta['title']} - {chapter['title']}",
                metadata={
                    "type": "textbook",
                    "book_title": book_meta["title"],
                    "book_author": book_meta["author"],
                    "chapter_number": chapter["number"],
                    "chapter_title": chapter["title"],
                },
            )
            total_chunks += chunks

        return total_chunks

    def add_syllabus(self, syllabus_content: str) -> int:
        """Add syllabus content."""
        return self.add_document(
            content=syllabus_content,
            source="Course Syllabus",
            metadata={"type": "syllabus"},
        )

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant content."""
        results = self.collection.query(query_texts=[query], n_results=n_results)

        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append(
                {
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": (
                        results["distances"][0][i] if "distances" in results else None
                    ),
                }
            )

        return output

    def get_stats(self) -> Dict:
        """Get collection statistics."""
        return {
            "collection": self.collection_name,
            "document_count": self.collection.count(),
            "course": self.course_code,
        }


def ingest_hb411_course():
    """Ingest all HB411 course materials."""

    course_dir = Path(r"D:\OsMEN\content\courses\HB411_HealthyBoundaries")
    chroma_path = str(course_dir / "embeddings" / "chroma_db")

    print("=" * 60)
    print("📚 HB411 Course Embeddings Ingestion")
    print("=" * 60)

    # Initialize embeddings
    embeddings = CourseEmbeddings("HB411", chroma_path)

    # Ingest extracted textbooks
    readings_dir = course_dir / "readings" / "raw"

    if readings_dir.exists():
        for textbook_dir in readings_dir.iterdir():
            if textbook_dir.is_dir() and (textbook_dir / "metadata.json").exists():
                print(f"\n📖 Processing: {textbook_dir.name}")
                chunks = embeddings.add_textbook(textbook_dir)
                print(f"   Added {chunks} chunks")

    # Ingest course data
    course_data_file = course_dir / "course_data.json"
    if course_data_file.exists():
        with open(course_data_file) as f:
            course_data = json.load(f)

        # Create syllabus text from course data
        syllabus_text = f"""
        Course: {course_data['course']['name']}
        Semester: {course_data['course']['semester']}
        Instructor: {course_data['instructor']['name']}
        
        Learning Outcomes:
        {chr(10).join(f'- {lo}' for lo in course_data['learning_outcomes'])}
        
        Schedule:
        {chr(10).join(f"Week {w['week']}: {w['topic']} ({w['date']})" for w in course_data['schedule'])}
        
        Assignments:
        {chr(10).join(f"- {a['name']} ({a['weight']})" for a in course_data['assignments'])}
        """

        chunks = embeddings.add_syllabus(syllabus_text)
        print(f"\n📋 Added syllabus: {chunks} chunks")

    # Final stats
    stats = embeddings.get_stats()
    print("\n" + "=" * 60)
    print("✅ Ingestion Complete!")
    print("=" * 60)
    print(f"Collection: {stats['collection']}")
    print(f"Total documents: {stats['document_count']}")

    # Test search
    print("\n🔍 Test Search: 'boundaries in ministry'")
    results = embeddings.search("boundaries in ministry", n_results=3)
    for i, r in enumerate(results):
        print(f"\n{i+1}. Source: {r['metadata'].get('source', 'Unknown')}")
        print(f"   Preview: {r['content'][:150]}...")

    return embeddings


if __name__ == "__main__":
    ingest_hb411_course()
