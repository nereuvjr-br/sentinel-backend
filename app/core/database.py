from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.core.config import settings

# Ajusta a URL para o driver Async se o usuário tiver colocado postgresql://
# O SQLAlchemy Async requer postgresql+asyncpg://
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    db_url,
    echo=(settings.ENV == "dev"),  # Loga SQL no terminal em modo DEV
    future=True
)

async def init_db():
    """Função utilitária para criar as tabelas (apenas para DEV/Testes rápidos).
    Em produção, use Alembic."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    """Dependency injection para FastAPI."""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
