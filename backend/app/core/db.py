"""
Database Configuration, Engine & Base Models
Supports both PostgreSQL (production) and SQLite (fast local testing/CI) with async SQLAlchemy 2.x.
"""
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from sqlalchemy import DateTime, String, ForeignKey, Index
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from backend.app.core.config import settings

# Engine configuration
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
}

# If using SQLite, add check_same_thread=False
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


class UUIDBase(Base):
    """Abstract base model with non-guessable UUID primary key and UTC timestamps."""
    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class TenantMixin:
    """Every school-owned row carries school_id with an indexed tenant boundary."""
    school_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Ensure all domain models are loaded into SQLAlchemy's class registry
def _load_all_models():
    import backend.app.tenancy.models  # noqa: F401
    import backend.app.identity.models  # noqa: F401
    import backend.app.academics.models  # noqa: F401
    import backend.app.content.models  # noqa: F401
    import backend.app.generation.models  # noqa: F401
    import backend.app.assessments.models  # noqa: F401
    import backend.app.audit.models  # noqa: F401
    import backend.app.notifications.models  # noqa: F401

_load_all_models()

