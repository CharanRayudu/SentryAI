"""
Weaviate Vector Database Service
Handles RAG document storage and semantic search
"""
import os
from typing import Optional, Dict, Any, List
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery


class WeaviateService:
    """Wrapper for Weaviate vector database operations"""
    
    def __init__(self):
        self._client: Optional[weaviate.WeaviateClient] = None
        self._url = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    
    def connect(self) -> weaviate.WeaviateClient:
        """Get or create Weaviate client connection"""
        if self._client is None:
            self._client = weaviate.connect_to_custom(
                http_host=self._url.replace("http://", "").replace("https://", "").split(":")[0],
                http_port=int(self._url.split(":")[-1]) if ":" in self._url.split("/")[-1] else 8080,
                http_secure=self._url.startswith("https"),
                grpc_host=self._url.replace("http://", "").replace("https://", "").split(":")[0],
                grpc_port=50051,
                grpc_secure=False,
            )
        return self._client
    
    def disconnect(self):
        """Close client connection"""
        if self._client:
            self._client.close()
            self._client = None

    # --- Collection Management ---
    
    def ensure_collection(self, collection_name: str = "SentryDocuments"):
        """Ensure the documents collection exists"""
        client = self.connect()
        
        if not client.collections.exists(collection_name):
            client.collections.create(
                name=collection_name,
                properties=[
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="document_id", data_type=DataType.TEXT),
                    Property(name="project_id", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT),
                    Property(name="file_name", data_type=DataType.TEXT),
                    Property(name="file_type", data_type=DataType.TEXT),
                    Property(name="metadata", data_type=DataType.OBJECT),
                ],
                # Using no vectorizer - we'll provide embeddings externally
                vectorizer_config=Configure.Vectorizer.none(),
            )
        
        return client.collections.get(collection_name)

    # --- Document Operations ---
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        collection_name: str = "SentryDocuments"
    ) -> int:
        """
        Add document chunks with their embeddings.
        
        Args:
            chunks: List of chunk data with content, document_id, etc.
            embeddings: Corresponding embedding vectors
            collection_name: Target collection
        
        Returns:
            Number of chunks added
        """
        collection = self.ensure_collection(collection_name)
        
        with collection.batch.dynamic() as batch:
            for chunk, embedding in zip(chunks, embeddings):
                batch.add_object(
                    properties={
                        "content": chunk["content"],
                        "document_id": chunk["document_id"],
                        "project_id": chunk["project_id"],
                        "chunk_index": chunk.get("chunk_index", 0),
                        "file_name": chunk.get("file_name", ""),
                        "file_type": chunk.get("file_type", ""),
                        "metadata": chunk.get("metadata", {}),
                    },
                    vector=embedding
                )
        
        return len(chunks)
    
    def delete_document_chunks(
        self,
        document_id: str,
        collection_name: str = "SentryDocuments"
    ) -> bool:
        """Delete all chunks for a document"""
        collection = self.ensure_collection(collection_name)
        
        # Delete by filter
        collection.data.delete_many(
            where=weaviate.classes.query.Filter.by_property("document_id").equal(document_id)
        )
        
        return True

    # --- Search Operations ---
    
    def semantic_search(
        self,
        query_vector: List[float],
        project_id: str,
        limit: int = 10,
        collection_name: str = "SentryDocuments"
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using a query vector.
        
        Args:
            query_vector: Embedding of the search query
            project_id: Filter by project
            limit: Max results to return
        
        Returns:
            List of matching chunks with scores
        """
        collection = self.ensure_collection(collection_name)
        
        results = collection.query.near_vector(
            near_vector=query_vector,
            limit=limit,
            filters=weaviate.classes.query.Filter.by_property("project_id").equal(project_id),
            return_metadata=MetadataQuery(distance=True),
        )
        
        return [
            {
                "content": obj.properties.get("content"),
                "document_id": obj.properties.get("document_id"),
                "file_name": obj.properties.get("file_name"),
                "chunk_index": obj.properties.get("chunk_index"),
                "score": 1 - obj.metadata.distance if obj.metadata.distance else 0,
                "metadata": obj.properties.get("metadata", {}),
            }
            for obj in results.objects
        ]
    
    def hybrid_search(
        self,
        query: str,
        query_vector: List[float],
        project_id: str,
        limit: int = 10,
        alpha: float = 0.5,
        collection_name: str = "SentryDocuments"
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining keyword and semantic search.
        
        Args:
            query: Text query for keyword matching
            query_vector: Embedding for semantic matching
            project_id: Filter by project
            limit: Max results
            alpha: Balance between keyword (0) and vector (1) search
        """
        collection = self.ensure_collection(collection_name)
        
        results = collection.query.hybrid(
            query=query,
            vector=query_vector,
            alpha=alpha,
            limit=limit,
            filters=weaviate.classes.query.Filter.by_property("project_id").equal(project_id),
            return_metadata=MetadataQuery(score=True),
        )
        
        return [
            {
                "content": obj.properties.get("content"),
                "document_id": obj.properties.get("document_id"),
                "file_name": obj.properties.get("file_name"),
                "chunk_index": obj.properties.get("chunk_index"),
                "score": obj.metadata.score if obj.metadata.score else 0,
                "metadata": obj.properties.get("metadata", {}),
            }
            for obj in results.objects
        ]

    # --- RAG Context Retrieval ---
    
    def get_context_for_query(
        self,
        query_vector: List[float],
        project_id: str,
        max_chunks: int = 5,
        max_tokens: int = 4000,
        collection_name: str = "SentryDocuments"
    ) -> str:
        """
        Retrieve relevant context for RAG.
        
        Args:
            query_vector: Embedding of the user query
            project_id: Project scope
            max_chunks: Maximum number of chunks to retrieve
            max_tokens: Approximate token limit
        
        Returns:
            Concatenated context string
        """
        results = self.semantic_search(
            query_vector=query_vector,
            project_id=project_id,
            limit=max_chunks,
            collection_name=collection_name
        )
        
        context_parts = []
        total_chars = 0
        char_limit = max_tokens * 4  # Rough estimate: 1 token ≈ 4 chars
        
        for result in results:
            content = result["content"]
            if total_chars + len(content) > char_limit:
                # Truncate last chunk if needed
                remaining = char_limit - total_chars
                if remaining > 100:
                    context_parts.append(content[:remaining] + "...")
                break
            
            context_parts.append(f"[Source: {result['file_name']}]\n{content}")
            total_chars += len(content)
        
        return "\n\n---\n\n".join(context_parts)

    # --- Statistics ---
    
    def get_document_count(
        self,
        project_id: str,
        collection_name: str = "SentryDocuments"
    ) -> int:
        """Get count of chunks for a project"""
        collection = self.ensure_collection(collection_name)
        
        result = collection.aggregate.over_all(
            filters=weaviate.classes.query.Filter.by_property("project_id").equal(project_id),
            total_count=True
        )
        
        return result.total_count or 0
    
    def list_documents(
        self,
        project_id: str,
        collection_name: str = "SentryDocuments"
    ) -> List[str]:
        """Get list of unique document IDs for a project"""
        collection = self.ensure_collection(collection_name)
        
        # Group by document_id
        results = collection.query.fetch_objects(
            filters=weaviate.classes.query.Filter.by_property("project_id").equal(project_id),
            limit=1000,
        )
        
        document_ids = set()
        for obj in results.objects:
            doc_id = obj.properties.get("document_id")
            if doc_id:
                document_ids.add(doc_id)
        
        return list(document_ids)


# Singleton instance
weaviate_service = WeaviateService()

