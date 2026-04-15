import boto3
import uuid
from datetime import datetime, timezone
from app.core.config import get_settings

settings = get_settings()


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name="us-east-1",
    )


def generate_storage_key(filename: str) -> str:
    now = datetime.now(timezone.utc)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    unique_id = uuid.uuid4().hex[:12]
    return f"reports/{now.year}/{now.month:02d}/{unique_id}.{ext}"


def generate_presigned_upload_url(storage_key: str, content_type: str) -> str:
    client = get_s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET_NAME,
            "Key": storage_key,
            "ContentType": content_type,
        },
        ExpiresIn=settings.S3_PRESIGNED_EXPIRY,
    )
    # boto3 embeds the internal endpoint hostname; replace with the public one
    # so the browser can reach MinIO directly (e.g. minio:9000 → localhost:9000)
    if settings.S3_ENDPOINT_URL != settings.S3_PUBLIC_URL:
        url = url.replace(settings.S3_ENDPOINT_URL, settings.S3_PUBLIC_URL, 1)
    return url


def check_object_exists(storage_key: str) -> bool:
    client = get_s3_client()
    try:
        client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=storage_key)
        return True
    except client.exceptions.ClientError:
        return False


def get_public_url(storage_key: str) -> str:
    return f"{settings.S3_PUBLIC_URL}/{settings.S3_BUCKET_NAME}/{storage_key}"


def ensure_bucket_exists():
    client = get_s3_client()
    try:
        client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except client.exceptions.ClientError:
        client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
