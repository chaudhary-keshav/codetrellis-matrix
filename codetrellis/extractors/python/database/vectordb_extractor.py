"""
VectorDBExtractor - Extracts Vector Database components.

This extractor parses Python code using vector databases and extracts:
- Pinecone collections and indexes
- ChromaDB collections
- Qdrant collections and points
- Weaviate classes and schema
- FAISS indexes
- Milvus collections

Part of CodeTrellis v2.0 - Python AI/ML Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class VectorCollectionInfo:
    """Information about a vector database collection."""
    name: str
    provider: str  # pinecone, chroma, qdrant, weaviate, faiss, milvus
    dimension: Optional[int] = None
    metric: Optional[str] = None  # cosine, euclidean, dot_product
    index_type: Optional[str] = None
    metadata_fields: List[str] = field(default_factory=list)
    line_number: int = 0


@dataclass
class VectorIndexInfo:
    """Information about a vector index."""
    name: str
    provider: str
    dimension: Optional[int] = None
    metric: Optional[str] = None
    shards: Optional[int] = None
    replicas: Optional[int] = None
    cloud: Optional[str] = None
    region: Optional[str] = None


@dataclass
class VectorQueryInfo:
    """Information about a vector query/search operation."""
    collection: str
    query_type: str  # similarity_search, query, search
    top_k: Optional[int] = None
    filters: List[str] = field(default_factory=list)
    include_metadata: bool = True


@dataclass
class EmbeddingModelInfo:
    """Information about embedding model usage."""
    name: str
    provider: str  # openai, huggingface, sentence-transformers
    model_name: Optional[str] = None
    dimension: Optional[int] = None


class VectorDBExtractor:
    """
    Extracts vector database-related components from Python source code.

    Handles:
    - Pinecone index and collection operations
    - ChromaDB client and collections
    - Qdrant client and operations
    - Weaviate client and schema
    - FAISS index operations
    - Milvus collections
    - Embedding model configurations
    """

    # Pinecone patterns
    PINECONE_INDEX_PATTERN = re.compile(
        r'(?:pinecone\.)?(?:Index|create_index)\s*\(\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    PINECONE_INIT_PATTERN = re.compile(
        r'pinecone\.init\s*\(\s*api_key\s*=\s*([^,)]+)',
        re.MULTILINE
    )

    # ChromaDB patterns
    CHROMA_CLIENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*chromadb\.(?:Client|PersistentClient|HttpClient)\s*\(',
        re.MULTILINE
    )

    CHROMA_COLLECTION_PATTERN = re.compile(
        r'\.(?:create_collection|get_collection|get_or_create_collection)\s*\(\s*(?:name\s*=\s*)?[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Qdrant patterns
    QDRANT_CLIENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*QdrantClient\s*\(',
        re.MULTILINE
    )

    QDRANT_COLLECTION_PATTERN = re.compile(
        r'\.(?:create_collection|recreate_collection)\s*\(\s*collection_name\s*=\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Weaviate patterns
    WEAVIATE_CLIENT_PATTERN = re.compile(
        r'(\w+)\s*=\s*weaviate\.Client\s*\(',
        re.MULTILINE
    )

    WEAVIATE_CLASS_PATTERN = re.compile(
        r'[\'"]class[\'"]\s*:\s*[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # FAISS patterns
    FAISS_INDEX_PATTERN = re.compile(
        r'(\w+)\s*=\s*faiss\.(?:IndexFlatL2|IndexFlatIP|IndexIVFFlat|IndexHNSWFlat)\s*\(\s*(\d+)',
        re.MULTILINE
    )

    # Milvus patterns
    MILVUS_COLLECTION_PATTERN = re.compile(
        r'Collection\s*\(\s*(?:name\s*=\s*)?[\'"](\w+)[\'"]',
        re.MULTILINE
    )

    # Embedding patterns
    OPENAI_EMBEDDING_PATTERN = re.compile(
        r'OpenAIEmbeddings\s*\(\s*(?:model\s*=\s*[\'"]([^"\']+)[\'"])?',
        re.MULTILINE
    )

    SENTENCE_TRANSFORMER_PATTERN = re.compile(
        r'SentenceTransformer\s*\(\s*[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    HF_EMBEDDING_PATTERN = re.compile(
        r'HuggingFaceEmbeddings\s*\(\s*(?:model_name\s*=\s*)?[\'"]([^"\']+)[\'"]',
        re.MULTILINE
    )

    # Vector dimension patterns
    DIMENSION_PATTERN = re.compile(
        r'(?:dimension|dim|dimensions|embedding_dim)\s*[=:]\s*(\d+)',
        re.IGNORECASE
    )

    # Metric patterns
    METRIC_PATTERN = re.compile(
        r'(?:metric|distance|distance_metric|similarity)\s*[=:]\s*[\'"]?(cosine|euclidean|dot_product|l2|ip)[\'"]?',
        re.IGNORECASE
    )

    def __init__(self):
        """Initialize the VectorDB extractor."""
        pass

    def extract(self, content: str) -> Dict[str, Any]:
        """
        Extract all vector database components from Python content.

        Args:
            content: Python source code

        Returns:
            Dict with collections, indexes, queries, embeddings
        """
        collections = self._extract_collections(content)
        indexes = self._extract_indexes(content)
        queries = self._extract_queries(content)
        embeddings = self._extract_embeddings(content)

        return {
            'collections': collections,
            'indexes': indexes,
            'queries': queries,
            'embeddings': embeddings
        }

    def _extract_collections(self, content: str) -> List[VectorCollectionInfo]:
        """Extract vector database collection definitions."""
        collections = []

        # ChromaDB collections
        for match in self.CHROMA_COLLECTION_PATTERN.finditer(content):
            coll_name = match.group(1)
            context = content[match.start():match.start()+300]

            dim = None
            dim_match = self.DIMENSION_PATTERN.search(context)
            if dim_match:
                dim = int(dim_match.group(1))

            metric = "cosine"  # Default for ChromaDB
            metric_match = self.METRIC_PATTERN.search(context)
            if metric_match:
                metric = metric_match.group(1).lower()

            collections.append(VectorCollectionInfo(
                name=coll_name,
                provider="chromadb",
                dimension=dim,
                metric=metric,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Qdrant collections
        for match in self.QDRANT_COLLECTION_PATTERN.finditer(content):
            coll_name = match.group(1)
            context = content[match.start():match.start()+500]

            dim = None
            dim_match = re.search(r'size\s*=\s*(\d+)', context)
            if dim_match:
                dim = int(dim_match.group(1))

            metric = None
            metric_match = re.search(r'distance\s*=\s*Distance\.(\w+)', context)
            if metric_match:
                metric = metric_match.group(1).lower()

            collections.append(VectorCollectionInfo(
                name=coll_name,
                provider="qdrant",
                dimension=dim,
                metric=metric,
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Weaviate classes
        for match in self.WEAVIATE_CLASS_PATTERN.finditer(content):
            class_name = match.group(1)
            collections.append(VectorCollectionInfo(
                name=class_name,
                provider="weaviate",
                line_number=content[:match.start()].count('\n') + 1
            ))

        # Milvus collections
        for match in self.MILVUS_COLLECTION_PATTERN.finditer(content):
            coll_name = match.group(1)
            context = content[match.start():match.start()+500]

            dim = None
            dim_match = self.DIMENSION_PATTERN.search(context)
            if dim_match:
                dim = int(dim_match.group(1))

            collections.append(VectorCollectionInfo(
                name=coll_name,
                provider="milvus",
                dimension=dim,
                line_number=content[:match.start()].count('\n') + 1
            ))

        return collections

    def _extract_indexes(self, content: str) -> List[VectorIndexInfo]:
        """Extract vector index definitions."""
        indexes = []

        # Pinecone indexes
        for match in self.PINECONE_INDEX_PATTERN.finditer(content):
            index_name = match.group(1)
            context = content[match.start():match.start()+500]

            dim = None
            dim_match = self.DIMENSION_PATTERN.search(context)
            if dim_match:
                dim = int(dim_match.group(1))

            metric = None
            metric_match = self.METRIC_PATTERN.search(context)
            if metric_match:
                metric = metric_match.group(1).lower()

            # Cloud/region info
            cloud_match = re.search(r'cloud\s*=\s*[\'"](\w+)[\'"]', context)
            region_match = re.search(r'region\s*=\s*[\'"]([^"\']+)[\'"]', context)

            indexes.append(VectorIndexInfo(
                name=index_name,
                provider="pinecone",
                dimension=dim,
                metric=metric,
                cloud=cloud_match.group(1) if cloud_match else None,
                region=region_match.group(1) if region_match else None
            ))

        # FAISS indexes
        for match in self.FAISS_INDEX_PATTERN.finditer(content):
            var_name = match.group(1)
            dim = int(match.group(2))

            # Determine index type from the constructor
            full_match = match.group(0)
            index_type = "flat_l2"
            if "IndexFlatIP" in full_match:
                index_type = "flat_ip"
            elif "IndexIVFFlat" in full_match:
                index_type = "ivf_flat"
            elif "IndexHNSWFlat" in full_match:
                index_type = "hnsw"

            indexes.append(VectorIndexInfo(
                name=var_name,
                provider="faiss",
                dimension=dim,
                metric="l2" if "L2" in index_type else "ip"
            ))

        return indexes

    def _extract_queries(self, content: str) -> List[VectorQueryInfo]:
        """Extract vector query/search operations."""
        queries = []

        # Similarity search patterns
        similarity_patterns = [
            # LangChain vectorstore
            (r'(\w+)\.similarity_search\s*\(', 'similarity_search'),
            # ChromaDB query
            (r'(\w+)\.query\s*\(', 'query'),
            # Qdrant search
            (r'(\w+)\.search\s*\(', 'search'),
            # Pinecone query
            (r'(\w+)\.query\s*\(', 'query'),
        ]

        for pattern, query_type in similarity_patterns:
            for match in re.finditer(pattern, content):
                collection = match.group(1)
                context = content[match.start():match.start()+200]

                # Extract top_k
                top_k = None
                k_match = re.search(r'(?:k|top_k|limit)\s*=\s*(\d+)', context)
                if k_match:
                    top_k = int(k_match.group(1))

                queries.append(VectorQueryInfo(
                    collection=collection,
                    query_type=query_type,
                    top_k=top_k
                ))

        return queries

    def _extract_embeddings(self, content: str) -> List[EmbeddingModelInfo]:
        """Extract embedding model configurations."""
        embeddings = []

        # OpenAI embeddings
        for match in self.OPENAI_EMBEDDING_PATTERN.finditer(content):
            model = match.group(1) or "text-embedding-ada-002"
            embeddings.append(EmbeddingModelInfo(
                name="openai_embeddings",
                provider="openai",
                model_name=model,
                dimension=1536 if "ada-002" in model else None
            ))

        # Sentence Transformers
        for match in self.SENTENCE_TRANSFORMER_PATTERN.finditer(content):
            model = match.group(1)
            embeddings.append(EmbeddingModelInfo(
                name="sentence_transformer",
                provider="sentence-transformers",
                model_name=model
            ))

        # HuggingFace embeddings
        for match in self.HF_EMBEDDING_PATTERN.finditer(content):
            model = match.group(1)
            embeddings.append(EmbeddingModelInfo(
                name="hf_embeddings",
                provider="huggingface",
                model_name=model
            ))

        return embeddings

    def to_codetrellis_format(self, result: Dict[str, Any]) -> str:
        """Convert extracted vector DB data to CodeTrellis format."""
        lines = []

        # Collections
        collections = result.get('collections', [])
        if collections:
            lines.append("[VECTOR_COLLECTIONS]")
            for coll in collections:
                parts = [f"{coll.name}|provider:{coll.provider}"]
                if coll.dimension:
                    parts.append(f"dim:{coll.dimension}")
                if coll.metric:
                    parts.append(f"metric:{coll.metric}")
                lines.append("|".join(parts))
            lines.append("")

        # Indexes
        indexes = result.get('indexes', [])
        if indexes:
            lines.append("[VECTOR_INDEXES]")
            for idx in indexes:
                parts = [f"{idx.name}|provider:{idx.provider}"]
                if idx.dimension:
                    parts.append(f"dim:{idx.dimension}")
                if idx.metric:
                    parts.append(f"metric:{idx.metric}")
                if idx.cloud:
                    parts.append(f"cloud:{idx.cloud}")
                if idx.region:
                    parts.append(f"region:{idx.region}")
                lines.append("|".join(parts))
            lines.append("")

        # Embeddings
        embeddings = result.get('embeddings', [])
        if embeddings:
            lines.append("[EMBEDDING_MODELS]")
            for emb in embeddings:
                parts = [f"{emb.provider}"]
                if emb.model_name:
                    parts.append(f"model:{emb.model_name}")
                if emb.dimension:
                    parts.append(f"dim:{emb.dimension}")
                lines.append("|".join(parts))
            lines.append("")

        # Queries (summarized)
        queries = result.get('queries', [])
        if queries:
            lines.append("[VECTOR_OPERATIONS]")
            # Group by collection
            by_collection = {}
            for q in queries:
                if q.collection not in by_collection:
                    by_collection[q.collection] = []
                by_collection[q.collection].append(q.query_type)

            for coll, ops in by_collection.items():
                unique_ops = list(set(ops))
                lines.append(f"{coll}|ops:[{','.join(unique_ops)}]")

        return "\n".join(lines)


# Convenience function
def extract_vectordb(content: str) -> Dict[str, Any]:
    """Extract vector database components from Python content."""
    extractor = VectorDBExtractor()
    return extractor.extract(content)
