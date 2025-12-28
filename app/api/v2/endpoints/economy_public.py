from fastapi import APIRouter, Depends
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.services.public_economy_service import PublicEconomyService

router = APIRouter()

import traceback

@router.get("/dashboard")
async def get_public_economy_dashboard(session: AsyncSession = Depends(get_session)):
    """
    Retorna dados agregados e seguros para o dashboard público de economia.
    Cacheado por 5 minutos server-side.
    """
    try:
        return await PublicEconomyService.get_dashboard_summary(session)
    except Exception as e:
        tb = traceback.format_exc()
        print(f"❌ ERRO CRÍTICO NO DASHBOARD: {e}")
        return fastapi.responses.JSONResponse(
            status_code=500,
            content={"detail": f"Server Error: {str(e)}", "traceback": tb}
        )
