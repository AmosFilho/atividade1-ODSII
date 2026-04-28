from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import get_rag_pipeline
from app.core.config import settings
from app.rag.pipeline import RAGPipeline
from app.schemas.documents import (
    ClearCollectionResponse,
    DeleteDocumentResponse,
    DocumentListResponse,
    IngestResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".html", ".htm"}


@router.post("/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    rag: RAGPipeline = Depends(get_rag_pipeline),
) -> IngestResponse:
    filename = Path(file.filename or "document").name
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato nao suportado: {extension}. Envie PDF, TXT, MD ou HTML.",
        )

    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    target_path = settings.raw_data_dir / f"{uuid4().hex}_{filename}"
    content = await file.read()
    target_path.write_bytes(content)

    try:
        return rag.ingest_file(target_path, original_filename=filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/ingest-samples", response_model=IngestResponse)
def ingest_samples(rag: RAGPipeline = Depends(get_rag_pipeline)) -> IngestResponse:
    sample_dir = settings.sample_data_dir
    files = sorted(
        path
        for path in sample_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if not files:
        raise HTTPException(status_code=404, detail="Nenhum documento de exemplo encontrado.")

    total_chunks = 0
    document_ids: list[str] = []
    for path in files:
        result = rag.ingest_file(path, original_filename=path.name)
        total_chunks += result.chunks_indexed
        document_ids.extend(result.document_ids)

    return IngestResponse(
        message=f"{len(files)} documentos de exemplo indexados.",
        chunks_indexed=total_chunks,
        document_ids=document_ids,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(rag: RAGPipeline = Depends(get_rag_pipeline)) -> DocumentListResponse:
    return rag.list_documents()


@router.delete("/{source_id}", response_model=DeleteDocumentResponse)
def delete_document(
    source_id: str,
    rag: RAGPipeline = Depends(get_rag_pipeline),
) -> DeleteDocumentResponse:
    deleted = rag.delete_document(source_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Documento nao encontrado.")
    return DeleteDocumentResponse(source_id=source_id, deleted_chunks=deleted)


@router.delete("", response_model=ClearCollectionResponse)
def clear_documents(rag: RAGPipeline = Depends(get_rag_pipeline)) -> ClearCollectionResponse:
    deleted = rag.clear()
    return ClearCollectionResponse(message="Base vetorial limpa.", deleted_chunks=deleted)

