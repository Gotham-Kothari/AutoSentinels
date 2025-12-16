from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class TelemetryPayload(BaseModel):
    vin: str = Field(..., description="Vehicle Identification Number")
    timestamp: datetime = Field(..., description="Event timestamp in ISO 8601")
    coolant_temp_c: float = Field(..., ge=-40, le=200)
    coolant_pressure_bar: float = Field(..., ge=0, le=5)
    engine_rpm: int = Field(..., ge=0, le=9000)
    vibration_level: float = Field(..., ge=0, le=100)
    battery_voltage: float = Field(..., ge=0, le=24)
    odometer_km: float = Field(..., ge=0)

    # Optional fields for extensibility
    ambient_temp_c: Optional[float] = Field(None, ge=-50, le=70)

    @field_validator("vin")
    @classmethod
    def vin_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("VIN cannot be empty")
        return v
