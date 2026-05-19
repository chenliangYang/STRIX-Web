"""Auth schemas."""

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Login request."""

    account: str
    password: str
    role: str = "admin"


class LoginResponse(BaseModel):
    """Login response."""

    token: str
    user: "UserInfo"


class UserInfo(BaseModel):
    """User info."""

    id: str
    username: str
    account: str
    role: str


LoginResponse.model_rebuild()
