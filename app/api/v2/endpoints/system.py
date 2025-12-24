from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlmodel import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.system_v2 import SentinelProcessedFile
from app.models.economy_v2 import SentinelUnparsedLog  # Assuming UnparsedLog is here for now, or move it to system

router = APIRouter()

@router.get("/files", response_model=List[SentinelProcessedFile])
async def get_processed_files(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=100),
    offset: int = 0,
    log_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """
    Get list of processed files (processes) with tracking info.
    """
    statement = select(SentinelProcessedFile)
    
    if log_type and log_type != "All":
        statement = statement.where(SentinelProcessedFile.log_type == log_type)
        
    if status and status != "All":
        statement = statement.where(SentinelProcessedFile.status == status)
        
    if search:
        statement = statement.where(SentinelProcessedFile.filename.contains(search))
        
    statement = statement.order_by(desc(SentinelProcessedFile.last_modified))
    statement = statement.offset(offset).limit(limit)
    
    result = await session.execute(statement)
    return result.scalars().all()

@router.get("/errors", response_model=List[SentinelUnparsedLog])
async def get_system_errors(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(50, le=100),
    offset: int = 0,
    log_type: Optional[str] = None
):
    """
    Get system errors and unparsed logs.
    """
    statement = select(SentinelUnparsedLog)
    
    if log_type and log_type != "All":
        statement = statement.where(SentinelUnparsedLog.log_type == log_type)
        
    statement = statement.order_by(desc(SentinelUnparsedLog.timestamp))
    statement = statement.offset(offset).limit(limit)
    
    result = await session.execute(statement)
    return result.scalars().all()
