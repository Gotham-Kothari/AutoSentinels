# backend/app/services/anomaly_detector.py

import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger("autosentinels")


class AnomalyResult(BaseModel):
    is_anomaly: bool
    component: Optional[str] = None
    severity: Optional[str] = None
    reason: Optional[str] = None
    predicted_failure_km: Optional[float] = None


class AnomalyDetector:
    """
    Deterministic, rule-based anomaly detector.

    Uses simple threshold logic on:
    - coolant_temp_c
    - coolant_pressure_bar
    - battery_voltage
    - engine_rpm
    - vibration_level

    Returns AnomalyResult which is compatible with:
    - ingest_telemetry()  (checks anomaly.is_anomaly)
    - CrewOrchestrator pipeline
    """

    @staticmethod
    async def detect(payload) -> AnomalyResult:
        # 1) Normalise payload into a dict
        if not isinstance(payload, dict):
            logger.info("Payload is NOT dict → converting via .dict()")
            try:
                payload = payload.dict()
            except Exception:
                logger.exception("Payload conversion to dict FAILED.")
                return AnomalyResult(is_anomaly=False)

        logger.info("=== [ANOMALY DETECTOR] Incoming telemetry payload ===")
        logger.info("PAYLOAD CONTENT: %s", payload)

        # 2) Extract fields with safe defaults
        coolant_temp = float(payload.get("coolant_temp_c") or 0.0)
        coolant_pressure = float(payload.get("coolant_pressure_bar") or 0.0)
        battery_voltage = float(payload.get("battery_voltage") or 12.5)
        rpm = int(payload.get("engine_rpm") or 0)
        vibration = float(payload.get("vibration_level") or 0.0)
        odometer = float(payload.get("odometer_km") or 0.0)

        # 3) Helper for predicted failure km based on severity
        def estimate_failure_km(base_odometer: float, severity: str) -> float:
            # This is a simple heuristic just for demo purposes
            increments = {
                "critical": 200.0,
                "high": 1000.0,
                "medium": 5000.0,
                "low": 15000.0,
            }
            inc = increments.get(severity, 8000.0)
            return base_odometer + inc

        # 4) Rule set (priority: safety-critical first)

        # --- Rule 1: Coolant / overheating issues (coolant_pump) ---
        # Very high coolant temperature or high temp + high pressure
        if coolant_temp >= 120 or (coolant_temp >= 110 and coolant_pressure >= 2.5):
            if coolant_temp >= 135:
                severity = "critical"
            elif coolant_temp >= 125:
                severity = "high"
            else:
                severity = "medium"

            reason_parts = []
            reason_parts.append(
                f"Coolant temperature is high at {coolant_temp:.1f}°C"
            )
            if coolant_pressure > 0:
                reason_parts.append(
                    f"with coolant pressure {coolant_pressure:.1f} bar"
                )
            reason_parts.append(
                "indicating poor coolant circulation or a failing coolant pump."
            )
            reason = " ".join(reason_parts)

            predicted_km = estimate_failure_km(odometer, severity)

            return AnomalyResult(
                is_anomaly=True,
                component="coolant_pump",
                severity=severity,
                reason=reason,
                predicted_failure_km=predicted_km,
            )

        # --- Rule 2: Electrical / charging issues (alternator) ---
        # Battery voltage significantly below normal operating range
        if battery_voltage <= 11.3:
            if battery_voltage <= 10.5:
                severity = "high"
            else:
                severity = "medium"

            reason = (
                f"Battery voltage is low at {battery_voltage:.1f} V, "
                "which suggests a charging system or alternator problem."
            )

            predicted_km = estimate_failure_km(odometer, severity)

            return AnomalyResult(
                is_anomaly=True,
                component="alternator",
                severity=severity,
                reason=reason,
                predicted_failure_km=predicted_km,
            )

        # --- Rule 3: High vibration under load (engine_misfire / turbocharger) ---
        if vibration >= 80 and rpm >= 2500:
            # If temperature is normal, lean toward engine misfire
            severity = "medium" if vibration < 95 else "high"

            reason = (
                f"Vibration level is high at {vibration:.1f} while engine RPM is {rpm}, "
                "indicating abnormal engine behaviour, likely an engine misfire under load."
            )

            predicted_km = estimate_failure_km(odometer, severity)

            return AnomalyResult(
                is_anomaly=True,
                component="engine_misfire",
                severity=severity,
                reason=reason,
                predicted_failure_km=predicted_km,
            )

        # --- Rule 4: Mild vibration at moderate RPM (sensor_failure) ---
        if vibration >= 60 and rpm < 2500:
            severity = "low"

            reason = (
                f"Vibration level is elevated at {vibration:.1f} with moderate RPM ({rpm}), "
                "which may indicate a sensor issue or minor imbalance rather than a major component failure."
            )

            predicted_km = estimate_failure_km(odometer, severity)

            return AnomalyResult(
                is_anomaly=True,
                component="sensor_failure",
                severity=severity,
                reason=reason,
                predicted_failure_km=predicted_km,
            )

        # --- Rule 5: No anomaly detected ---
        logger.info("[ANOMALY DETECTOR] No rule triggered → no anomaly.")
        return AnomalyResult(is_anomaly=False)
