"""Pydantic response shapes shared by the SmartRoad API."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class DetectionBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class DetectionRead(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    bbox: DetectionBox

class ComplaintRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: str
    title: str
    damage_types: list[str] = Field(default_factory=list)
    severity: str
    severity_score: float
    priority: str
    status: str
    latitude: float | None = None
    longitude: float | None = None
    address: str = ''
    confidence: float = 0
    damage_coverage: float = 0
    detection_count: int = 0
    detection_json: list[dict[str, Any]] = Field(default_factory=list)
    is_duplicate: bool = False
    duplicate_of: int | None = None
    is_demo: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None

class StatusUpdate(BaseModel):
    status: Literal['Reported', 'Verified', 'Assigned', 'In Progress', 'Repaired', 'Closed', 'Duplicate', 'Needs Review']

class RepairRead(BaseModel):
    id: int
    complaint_id: int
    before_coverage: float
    after_coverage: float
    improvement_percent: float
    verification_status: str
    verification_notes: str
    verified_at: datetime | None = None
    created_at: datetime | None = None
