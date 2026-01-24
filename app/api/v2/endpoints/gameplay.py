from datetime import datetime, timedelta

from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.config import settings
from sqlmodel import Session, select, func, desc
from sqlalchemy import Integer
from app.core.database import get_session
from app.models.gameplay_v2 import SentinelRaidMinigame, SentinelBunkerEvent


router = APIRouter()

@router.get("/raids", response_model=List[SentinelRaidMinigame])
async def get_raids(
    skip: int = 0,
    limit: int = 100,
    minigame: Optional[str] = None,
    attacker_id: Optional[str] = None,
    target_id: Optional[str] = None,
    success: Optional[bool] = None,
    raid_type: str = Query("player", enum=["player", "world", "all"]),
    session: Session = Depends(get_session)
    # user: Any = Depends(get_current_user) # Public for now or handled by frontend auth
):
    query = select(SentinelRaidMinigame)
    
    if minigame:
        query = query.where(SentinelRaidMinigame.minigame_class.contains(minigame))
    if attacker_id:
        query = query.where(SentinelRaidMinigame.attacker_steam_id == attacker_id)
    if target_id:
        query = query.where(SentinelRaidMinigame.target_owner_steam_id == target_id)
    if success is not None:
        query = query.where(SentinelRaidMinigame.is_success == success)
    
    # Filter by Raid Type
    if raid_type == "player":
        query = query.where(SentinelRaidMinigame.target_owner_steam_id != None)
    elif raid_type == "world":
        query = query.where(SentinelRaidMinigame.target_owner_steam_id == None)
        
    # Apply time delay if configured
    if settings.RAID_LOG_DELAY_MINUTES > 0:
        delay_threshold = datetime.utcnow() - timedelta(minutes=settings.RAID_LOG_DELAY_MINUTES)
        query = query.where(SentinelRaidMinigame.timestamp <= delay_threshold)
        
    query = query.order_by(desc(SentinelRaidMinigame.timestamp)).offset(skip).limit(limit)
    
    result = await session.execute(query)
    raids = result.scalars().all()
    
    # Mask sensitive data
    masked_raids = []
    for raid in raids:
        # We need to create a copy or modify the object before returning if it's not detached.
        # However, SQLModel objects returned from session might need refresh to be modified if part of session.
        # But for read-only response we can just modify attributes if we are careful or return a new list.
        # Since pydantic will serialize, modifying the object works.
        if raid.target_owner_name:
            raid.target_owner_name = "🔒 Área Protegida"
        if raid.target_owner_steam_id:
            raid.target_owner_steam_id = "HIDDEN"
        masked_raids.append(raid)
        
    return masked_raids

@router.get("/raids/stats")
async def get_raid_stats(
    raid_type: str = Query("player", enum=["player", "world", "all"]),
    session: Session = Depends(get_session)
):
    """
    Raid statistics with failed_attempts included in total count.
    Each failed_attempt during lockpicking counts as a separate invasion attempt.
    """
    
    # Helper to apply type filter to any query
    def apply_filter(q):
        if raid_type == "player":
            return q.where(SentinelRaidMinigame.target_owner_steam_id != None)
        elif raid_type == "world":
            return q.where(SentinelRaidMinigame.target_owner_steam_id == None)
        return q

    # 1. Total Raids vs Success Rate
    # Total attempts = number of raid events + sum of all failed_attempts
    total_events_query = apply_filter(select(func.count(SentinelRaidMinigame.id)))
    total_failed_query = apply_filter(select(func.sum(SentinelRaidMinigame.failed_attempts)))
    success_query = apply_filter(select(func.count(SentinelRaidMinigame.id)).where(SentinelRaidMinigame.is_success == True))
    
    total_events = (await session.execute(total_events_query)).scalar_one()
    total_failed = (await session.execute(total_failed_query)).scalar_one() or 0
    total_attempts = total_events + total_failed
    success_count = (await session.execute(success_query)).scalar_one()
    
    # 2. Top Raiders (by total attempts including failed_attempts)
    top_raiders_stmt = apply_filter(select(
        SentinelRaidMinigame.attacker_name,
        func.count(SentinelRaidMinigame.id).label("raid_events"),
        func.sum(SentinelRaidMinigame.failed_attempts).label("total_fails"),
        func.sum(func.cast(SentinelRaidMinigame.is_success, Integer)).label("successful_raids")
    )).group_by(SentinelRaidMinigame.attacker_name)
    
    top_raiders_raw = (await session.execute(top_raiders_stmt)).all()
    # Sort by total attempts (events + fails) in Python
    top_raiders_sorted = sorted(
        top_raiders_raw, 
        key=lambda r: r[1] + (r[2] or 0), 
        reverse=True
    )[:5]
    
    # 3. Top Targets (Clans/Players)
    top_targets_stmt = apply_filter(select(
        SentinelRaidMinigame.target_owner_name,
        func.count(SentinelRaidMinigame.id).label("raid_events"),
        func.sum(SentinelRaidMinigame.failed_attempts).label("total_fails"),
        func.sum(func.cast(SentinelRaidMinigame.is_success, Integer)).label("breached_count")
    ).where(SentinelRaidMinigame.target_owner_name != None)).group_by(
        SentinelRaidMinigame.target_owner_name
    )
    
    top_targets_raw = (await session.execute(top_targets_stmt)).all()
    # Sort by total defenses (events + fails) in Python
    top_targets_sorted = sorted(
        top_targets_raw,
        key=lambda r: r[1] + (r[2] or 0),
        reverse=True
    )[:5]

    # 4. Lock Type Statistics
    lock_types = ['Basic', 'Medium', 'Advanced', 'DialLock']
    lock_stats = []
    top_raiders_by_lock = {}
    
    for lock_type in lock_types:
        # Total attempts for this lock type (events + failed_attempts)
        lock_events_query = apply_filter(select(func.count(SentinelRaidMinigame.id)).where(
            SentinelRaidMinigame.lock_type == lock_type
        ))
        lock_fails_query = apply_filter(select(func.sum(SentinelRaidMinigame.failed_attempts)).where(
            SentinelRaidMinigame.lock_type == lock_type
        ))
        success_lock_query = apply_filter(select(func.count(SentinelRaidMinigame.id)).where(
            SentinelRaidMinigame.lock_type == lock_type,
            SentinelRaidMinigame.is_success == True
        ))
        
        lock_events = (await session.execute(lock_events_query)).scalar_one()
        lock_fails = (await session.execute(lock_fails_query)).scalar_one() or 0
        total_lock_attempts = lock_events + lock_fails
        success_lock = (await session.execute(success_lock_query)).scalar_one()
        
        if lock_events > 0:
            lock_stats.append({
                "lock_type": lock_type,
                "total_attempts": total_lock_attempts,
                "successes": success_lock,
                "success_rate": round((success_lock / total_lock_attempts * 100), 2) if total_lock_attempts > 0 else 0
            })
            
            # Get top 10 raiders for this lock type
            top_raiders_lock_stmt = apply_filter(select(
                SentinelRaidMinigame.attacker_name,
                func.count(SentinelRaidMinigame.id).label("raid_events"),
                func.sum(SentinelRaidMinigame.failed_attempts).label("total_fails"),
                func.sum(func.cast(SentinelRaidMinigame.is_success, Integer)).label("successful_raids")
            ).where(
                SentinelRaidMinigame.lock_type == lock_type
            )).group_by(SentinelRaidMinigame.attacker_name).order_by(desc("successful_raids")).limit(10)
            
            top_raiders_lock_raw = (await session.execute(top_raiders_lock_stmt)).all()
            
            top_raiders_by_lock[lock_type] = [
                {
                    "name": r[0] or "Unknown", 
                    "attempts": r[1] + (r[2] or 0),  # events + failed_attempts
                    "successes": r[3],
                    "success_rate": round((r[3] / (r[1] + (r[2] or 0)) * 100), 2) if (r[1] + (r[2] or 0)) > 0 else 0
                } for r in top_raiders_lock_raw
            ]
    
    return {
        "overview": {
            "total_attempts": total_attempts,
            "success_rate": round((success_count / total_attempts * 100), 2) if total_attempts > 0 else 0,
            "success_count": success_count
        },
        "top_raiders": [
            {
                "name": r[0] or "Unknown", 
                "attempts": r[1] + (r[2] or 0),  # events + failed_attempts
                "successes": r[3]
            } for r in top_raiders_sorted
        ],
        "top_targets": [
            {
                "name": r[0] or "Unknown", 
                "defenses": r[1] + (r[2] or 0),  # events + failed_attempts
                "breaches": r[3]
            } for r in top_targets_sorted
        ],
        "lock_type_stats": lock_stats,
        "top_raiders_by_lock_type": top_raiders_by_lock
    }

@router.get("/bunkers", response_model=List[SentinelBunkerEvent])
async def get_bunkers(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session)
):
    query = select(SentinelBunkerEvent).order_by(desc(SentinelBunkerEvent.timestamp)).offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
