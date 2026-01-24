from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class SentinelVerificationCode(SQLModel, table=True):
    __tablename__ = "sentinel_verification_codes"

    id: Optional[int] = Field(default=None, primary_key=True)
    phone_number: str = Field(index=True)
    code: str
    is_verified: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    attempts: int = Field(default=0)
