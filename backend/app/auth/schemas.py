from pydantic import BaseModel, EmailStr
from uuid import UUID


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    name: str | None = None


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: UUID
    role: str
