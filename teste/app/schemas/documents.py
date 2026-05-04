from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class IngestResponse(BaseModel):
    message: str
    chunks_indexed: int
    document_ids: list[str]


class IndexedDocument(BaseModel):
    source_id: str
    filename: str
    chunks: int


class DocumentListResponse(BaseModel):
    documents: list[IndexedDocument]


class DeleteDocumentResponse(BaseModel):
    source_id: str
    deleted_chunks: int


class ClearCollectionResponse(BaseModel):
    message: str
    deleted_chunks: int

