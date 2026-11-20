"""Pydantic-схемы для валидации и сериализации данных API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class InspectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    filename: str
    verdict: str = Field(..., description="НОРМА | ВНИМАНИЕ | БРАК | ОШИБКА СИСТЕМЫ")
    area_px: int
    area_mm2: Optional[float] = None
    confidence: float
    calibrated: bool
    original_url: str
    mask_url: str
    overlay_url: str
    message: Optional[str] = None


class InspectionListResponse(BaseModel):
    items: List[InspectionResponse]
    total: int
    page: int
    limit: int


class HealthResponse(BaseModel):
    status: str
    db: str
    ml: str
    retention_days: int
    timestamp: datetime
