"""Модели SQLAlchemy для системы контроля коррозии."""

from datetime import datetime, timezone
import uuid

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, String

from src.backend.db import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    verdict = Column(String(64), nullable=False, index=True)
    area_px = Column(BigInteger, nullable=False, default=0)
    area_mm2 = Column(Float, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    calibrated = Column(Boolean, nullable=False, default=False)
    upload_path = Column(String(512), nullable=False)
    mask_path = Column(String(512), nullable=False)
    overlay_path = Column(String(512), nullable=False)
    message = Column(String(512), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filename": self.filename,
            "verdict": self.verdict,
            "area_px": self.area_px,
            "area_mm2": self.area_mm2,
            "confidence": self.confidence,
            "calibrated": self.calibrated,
            "upload_path": self.upload_path,
            "mask_path": self.mask_path,
            "overlay_path": self.overlay_path,
            "message": self.message,
        }
