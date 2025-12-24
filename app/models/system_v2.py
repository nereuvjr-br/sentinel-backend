from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, BigInteger

class SentinelProcessedFile(SQLModel, table=True):
    __tablename__ = "sentinel_processed_files"
    
    filename: str = Field(primary_key=True)
    log_type: str = Field(index=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Real-Time Tracking
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    processed_bytes: int = Field(default=0, sa_column=Column(BigInteger)) # Offset
    lines_processed: int = Field(default=0)
    
    status: str = Field(default="Completed")
