from __future__ import annotations
import asyncio
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.api.dependencies import rate_limit_documents
from app.api.dependencies.services import get_document_service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.schemas.base import APIResponse
from app.schemas.responses import DocumentData, DocumentListData
from app.services.document_service import DocumentService
router = APIRouter(prefix="/documents", tags=["Documents"])
def _owner_id(current_user: User | None) -> str | None:
    return current_user.id if current_user is not None else None
@router.post(
    "/upload",
    response_model=APIResponse[DocumentData],
    summary="Upload a PDF document",
    description=(
        "Parses, chunks, embeds and indexes an uploaded financial PDF. "
        "Returns the document record with page/chunk counts. Set "
        "``background=true`` to queue large documents and poll "
        "``GET /documents/jobs/{job_id}`` for the indexing outcome."
    ),
    dependencies=[Depends(rate_limit_documents)],
)
async def upload_document(
    file: UploadFile = File(...),
    background: bool = False,
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[DocumentData]:
    owner = _owner_id(current_user)
    if background:
        result = await asyncio.to_thread(service.upload_background, file, owner)
    else:
        result = await asyncio.to_thread(service.upload, file, owner_id=owner)
    return APIResponse.success_response(
        message="Document indexed successfully",
        data=DocumentData(**result),
    )
@router.get(
    "/jobs/{job_id}",
    response_model=APIResponse[dict],
    summary="Get background job status",
    description=(
        "Returns the lifecycle state (pending / running / completed / failed), "
        "timestamps and error message (if any) for a background job. "
        "Jobs are only visible to their owner."
    ),
    dependencies=[Depends(rate_limit_documents)],
)
async def get_job_status(
    job_id: str,
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[dict]:
    job = await asyncio.to_thread(service.get_job, job_id, _owner_id(current_user))
    if job is None:
        raise HTTPException(status_code=404, detail="Job was not found.")
    return APIResponse.success_response(
        message="Job status retrieved",
        data=job,
    )
@router.get(
    "",
    response_model=APIResponse[DocumentListData],
    summary="List indexed documents",
    description="Returns the user's document library with page/chunk counts.",
    dependencies=[Depends(rate_limit_documents)],
)
async def list_documents(
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[DocumentListData]:
    result = await asyncio.to_thread(service.list_documents, owner_id=_owner_id(current_user))
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
    dependencies=[Depends(rate_limit_documents)],
)
async def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
    current_user: User | None = Depends(get_current_user),
) -> APIResponse[dict]:
    result = await asyncio.to_thread(
        service.delete_document,
        document_id,
        owner_id=_owner_id(current_user),
    )
    return APIResponse.success_response(
        message="Document deleted",
        data=result,
    )