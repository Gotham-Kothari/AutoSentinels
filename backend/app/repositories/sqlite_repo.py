# app/repositories/sqlite_repo.py

from typing import List
from datetime import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, JSON, select

from app.config import settings
from app.repositories.base import FaultRepository
from app.models.faults import FaultRecord

Base = declarative_base()


class FaultORM(Base):
    __tablename__ = "faults"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    vin: Mapped[str] = mapped_column(String, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime)
    predicted_failure_km: Mapped[float] = mapped_column(Float)
    component: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    raw_payload: Mapped[dict] = mapped_column(JSON)


engine = create_async_engine(settings.sqlite_url, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    """Create tables if they do not exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class SQLiteFaultRepository(FaultRepository):
    """SQLite implementation of the FaultRepository interface."""

    async def save_fault(self, fault: FaultRecord) -> None:
        async with AsyncSessionLocal() as session:
            orm_obj = FaultORM(
                id=fault.id,
                vin=fault.vin,
                detected_at=fault.detected_at,
                predicted_failure_km=fault.predicted_failure_km,
                component=fault.component,
                severity=fault.severity,
                raw_payload=fault.raw_payload,
            )
            session.add(orm_obj)
            await session.commit()

    async def list_faults_for_vin(self, vin: str) -> List[FaultRecord]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FaultORM)
                .where(FaultORM.vin == vin)
                .order_by(FaultORM.detected_at.desc())
            )
            rows = result.scalars().all()
            return [self._to_model(r) for r in rows]

    async def list_recent_faults(self, limit: int = 50) -> List[FaultRecord]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(FaultORM)
                .order_by(FaultORM.detected_at.desc())
                .limit(limit)
            )
            rows = result.scalars().all()
            return [self._to_model(r) for r in rows]

    def _to_model(self, orm: FaultORM) -> FaultRecord:
        return FaultRecord(
            id=orm.id,
            vin=orm.vin,
            detected_at=orm.detected_at,
            predicted_failure_km=orm.predicted_failure_km,
            component=orm.component,
            severity=orm.severity,
            raw_payload=orm.raw_payload,
        )

async def get_fault_repo() -> FaultRepository:
    return SQLiteFaultRepository(db_path=str(settings.DATABASE_PATH))