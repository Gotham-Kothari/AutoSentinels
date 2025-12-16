from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class FaultRecord(BaseModel):
    id: str
    vin: str
    detected_at: datetime
    predicted_failure_km: float
    component: str
    severity: Literal["low", "medium", "high", "critical"]
    raw_payload: dict
