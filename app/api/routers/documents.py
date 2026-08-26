"""
Documents Router

This module defines the financial document library endpoints:

- ``POST /documents/upload``   — upload and index a PDF.
- ``GET /documents``           — list indexed documents.
- ``DELETE /documents/{id}``   — delete a document and its vectors.

Design Decisions:
    - **No business logic in routes**: Handlers delegate entirely to
      ``DocumentService``.
    - **Dependency injection**: ``DocumentService`` is injected via
      ``Depends(get_document_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[T]``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.dependencies.services import get_document_service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.schemas.base import APIResponse
from app.schemas.responses import DocumentData, DocumentListData
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Documents"])


def _owner_id(current_user: User | None) -> str | None:
    """Return the owner id for the caller (None when auth is disabled)."""
    return current_user.id if current_user is not None else None


@router.post(
    "/upload",
    response_model=APIResponse[DocumentData],
    summary="Upload a PDF document",
    description=(
        "Parses, chunks, embeds and indexes an uploaded financial PDF. "
        "Returns the document record with page/chunk counts."
    ),
)
async def upload_document(
    file: UploadFile = File(...),
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[DocumentData]:
    """
    Upload endpoint.

    Args:
        file: The multipart PDF file.
        service: Injected ``DocumentService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` containing the indexed document record.
    """
    result = service.upload(file, owner_id=_owner_id(current_user))

    return APIResponse.success_response(
        message="Document indexed successfully",
        data=DocumentData(**result),
    )


@router.get(
    "",
    response_model=APIResponse[DocumentListData],
    summary="List indexed documents",
    description="Returns the user's document library with page/chunk counts.",
)
async def list_documents(
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[DocumentListData]:
    """
    Document library endpoint.

    Args:
        service: Injected ``DocumentService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` containing the document library.
    """
    result = service.list_documents(owner_id=_owner_id(current_user))

    return APIResponse.success_response(
        message=f"{result['total']} documents found",
        data=DocumentListData(
            documents=[DocumentData(**record) for record in result["documents"]],
            total=result["total"],
        ),
    )


@router.delete(
    "/{document_id}",
    response_model=APIResponse[dict],
    summary="Delete a document",
    description="Removes a document's vectors and metadata from the index.",
)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[dict]:
    """
    Delete endpoint.

    Args:
        document_id: The document to delete.
        service: Injected ``DocumentService`` instance.
        current_user: The authenticated owner (``None`` when auth disabled).

    Returns:
        An ``APIResponse`` confirming deletion.
    """
    result = service.delete_document(
        document_id,
        owner_id=_owner_id(current_user),
    )

    return APIResponse.success_response(
        message="Document deleted",
        data=result,
    )
