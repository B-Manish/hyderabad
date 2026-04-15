from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import SignedUploadRequest, SignedUploadResponse
from app.services.storage import generate_storage_key, generate_presigned_upload_url
from app.core.config import get_settings

router = APIRouter(prefix="/uploads", tags=["uploads"])
settings = get_settings()


@router.post("/sign", response_model=SignedUploadResponse)
async def sign_upload(request: SignedUploadRequest):
    # Validate file size
    if request.file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_BYTES} bytes")

    storage_key = generate_storage_key(request.filename)
    upload_url = generate_presigned_upload_url(storage_key, request.content_type)

    return SignedUploadResponse(
        upload_url=upload_url,
        storage_key=storage_key,
        expires_in=settings.S3_PRESIGNED_EXPIRY,
    )
