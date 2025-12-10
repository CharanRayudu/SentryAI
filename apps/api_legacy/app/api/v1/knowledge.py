"""
Knowledge Base API Routes
Document upload, processing, and RAG operations
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import aiofiles

router = APIRouter()


# --- Configuration ---
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./storage/uploads")
ALLOWED_EXTENSIONS = {".yaml", ".yml", ".json", ".pdf", ".md", ".csv", ".txt"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# --- Request/Response Models ---

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: Optional[int] = 0
    created_at: datetime
    processed_at: Optional[datetime] = None


class DocumentStatus(BaseModel):
    id: str
    status: str  # pending, processing, indexed, failed
    chunk_count: Optional[int] = 0
    error_message: Optional[str] = None


class SearchQuery(BaseModel):
    query: str
    limit: int = 10
    file_types: Optional[List[str]] = None


class SearchResult(BaseModel):
    content: str
    document_id: str
    file_name: str
    chunk_index: int
    score: float


# --- In-Memory Store (Replace with DB in production) ---
documents_db: Dict[str, Dict] = {}


# --- Helper Functions ---

def get_file_extension(filename: str) -> str:
    """Get file extension in lowercase"""
    return os.path.splitext(filename)[1].lower()


async def save_upload(file: UploadFile, doc_id: str) -> str:
    """Save uploaded file to storage"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    ext = get_file_extension(file.filename)
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}{ext}")
    
    async with aiofiles.open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    return file_path


async def process_document(doc_id: str, file_path: str, file_type: str, project_id: str):
    """
    Background task to process and index a document.
    In production, this would trigger a Temporal workflow.
    """
    try:
        documents_db[doc_id]["status"] = "processing"
        
        # Simulate processing delay
        import asyncio
        await asyncio.sleep(2)
        
        # TODO: In production:
        # 1. Parse document based on file_type
        # 2. Chunk the content
        # 3. Generate embeddings using NVIDIA API
        # 4. Store in Weaviate
        
        # Mock success
        documents_db[doc_id]["status"] = "indexed"
        documents_db[doc_id]["chunk_count"] = 15  # Mock
        documents_db[doc_id]["processed_at"] = datetime.utcnow()
        
    except Exception as e:
        documents_db[doc_id]["status"] = "failed"
        documents_db[doc_id]["error_message"] = str(e)


# --- Routes ---

@router.post("/knowledge/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    project_id: str = Form(...)
):
    """
    Upload a document to the knowledge base.
    Supports: .yaml, .json, .pdf, .md, .csv
    """
    # Validate file extension
    ext = get_file_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Generate document ID
    doc_id = str(uuid.uuid4())
    
    # Save file
    try:
        file_path = await save_upload(file, doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create document record
    now = datetime.utcnow()
    file_type = ext.lstrip(".")
    
    documents_db[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "file_type": file_type,
        "file_size": file_size,
        "file_path": file_path,
        "project_id": project_id,
        "status": "pending",
        "chunk_count": 0,
        "created_at": now,
        "processed_at": None,
        "error_message": None,
    }
    
    # Start background processing
    background_tasks.add_task(process_document, doc_id, file_path, file_type, project_id)
    
    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        file_type=file_type,
        file_size=file_size,
        status="pending",
        created_at=now
    )


@router.get("/knowledge/{document_id}/status", response_model=DocumentStatus)
async def get_document_status(document_id: str):
    """Get processing status of a document"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    return DocumentStatus(
        id=document_id,
        status=doc["status"],
        chunk_count=doc.get("chunk_count", 0),
        error_message=doc.get("error_message")
    )


@router.get("/knowledge", response_model=List[DocumentResponse])
async def list_documents(
    project_id: Optional[str] = None,
    status: Optional[str] = None
):
    """List all documents, optionally filtered"""
    docs = list(documents_db.values())
    
    if project_id:
        docs = [d for d in docs if d.get("project_id") == project_id]
    
    if status:
        docs = [d for d in docs if d.get("status") == status]
    
    # Sort by created_at descending
    docs.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
    
    return [
        DocumentResponse(
            id=d["id"],
            filename=d["filename"],
            file_type=d["file_type"],
            file_size=d["file_size"],
            status=d["status"],
            chunk_count=d.get("chunk_count", 0),
            created_at=d["created_at"],
            processed_at=d.get("processed_at")
        )
        for d in docs
    ]


@router.delete("/knowledge/{document_id}")
async def delete_document(document_id: str):
    """Delete a document from the knowledge base"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    # Delete file
    try:
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    # TODO: Delete chunks from Weaviate
    # weaviate_service.delete_document_chunks(document_id)
    
    del documents_db[document_id]
    
    return {"status": "deleted", "document_id": document_id}


@router.post("/knowledge/search", response_model=List[SearchResult])
async def search_knowledge(
    search: SearchQuery,
    project_id: str
):
    """
    Semantic search across the knowledge base.
    Uses vector similarity to find relevant document chunks.
    """
    # TODO: In production:
    # 1. Generate embedding for query using NVIDIA API
    # 2. Search Weaviate for similar chunks
    # 3. Return ranked results
    
    # Mock results for now
    mock_results = [
        SearchResult(
            content="The authentication endpoint accepts JWT tokens in the Authorization header...",
            document_id="mock-doc-1",
            file_name="api_spec.yaml",
            chunk_index=0,
            score=0.92
        ),
        SearchResult(
            content="Known XSS vulnerability patterns include script injection through...",
            document_id="mock-doc-2",
            file_name="vulnerability_patterns.md",
            chunk_index=5,
            score=0.87
        ),
    ]
    
    return mock_results[:search.limit]


@router.get("/knowledge/{document_id}/content")
async def get_document_content(document_id: str, chunk_index: Optional[int] = None):
    """Get content of a document or specific chunk"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    # Read file content (for preview)
    try:
        async with aiofiles.open(doc["file_path"], "r") as f:
            content = await f.read()
            
        # Truncate for preview
        if len(content) > 10000:
            content = content[:10000] + "\n... (truncated)"
        
        return {
            "document_id": document_id,
            "filename": doc["filename"],
            "content": content
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read document: {str(e)}")


@router.post("/knowledge/{document_id}/reprocess")
async def reprocess_document(document_id: str, background_tasks: BackgroundTasks):
    """Reprocess a failed or outdated document"""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = documents_db[document_id]
    
    # Reset status
    doc["status"] = "pending"
    doc["error_message"] = None
    doc["chunk_count"] = 0
    
    # Start reprocessing
    background_tasks.add_task(
        process_document,
        document_id,
        doc["file_path"],
        doc["file_type"],
        doc["project_id"]
    )
    
    return {"status": "reprocessing", "document_id": document_id}

