from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.models.verification import SentinelVerificationCode
from app.services.evolution_api import evolution_service
from pydantic import BaseModel
from datetime import datetime, timedelta
import random
import string

router = APIRouter()

class VerificationRequest(BaseModel):
    phone_number: str

class VerificationCheck(BaseModel):
    phone_number: str
    code: str

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

@router.post("/send")
async def send_verification_code(
    data: VerificationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Gera e envia um código de verificação para o WhatsApp.
    """
    phone = data.phone_number.strip()
    
    # Validação básica
    if len(phone) < 10:
        raise HTTPException(status_code=400, detail="Número de telefone inválido.")

    # Gerar código
    code = generate_code()
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Salvar no banco
    # Verifica se já existe um ativo e invalida ou reutiliza? Vamos criar um novo sempre.
    verification = SentinelVerificationCode(
        phone_number=phone,
        code=code,
        expires_at=expires_at,
        is_verified=False
    )
    session.add(verification)
    await session.commit()

    # Enviar via WhatsApp
    message = f"🔒 Seu código de verificação do SCUM Sentinel é: *{code}*\n\nEle expira em 10 minutos."
    
    success = await evolution_service.send_message(phone, message)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao enviar mensagem pelo WhatsApp. Verifique se o número está correto e tem WhatsApp.")

    return {"status": "sent", "message": "Código enviado com sucesso."}

@router.post("/check")
async def check_verification_code(
    data: VerificationCheck,
    session: AsyncSession = Depends(get_session)
):
    """
    Verifica se o código fornecido está correto.
    """
    query = select(SentinelVerificationCode).where(
        SentinelVerificationCode.phone_number == data.phone_number,
        SentinelVerificationCode.code == data.code,
        SentinelVerificationCode.is_verified == False,
        SentinelVerificationCode.expires_at > datetime.utcnow()
    ).order_by(SentinelVerificationCode.created_at.desc())
    
    result = await session.execute(query)
    verification = result.scalars().first()
    
    if not verification:
        raise HTTPException(status_code=400, detail="Código inválido ou expirado.")
        
    # Marcar como verificado
    verification.is_verified = True
    session.add(verification)
    await session.commit()
    
    return {"status": "verified", "message": "Telefone verificado com sucesso."}
