import os
import json
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Environment config
BACKEND_URL = os.environ.get("AUTOSENTINELS_BACKEND_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 10


class BackendClient:
    def __init__(self, base_url: str = BACKEND_URL, timeout: int = REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None):
        resp = requests.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: Dict[str, Any]):
        resp = requests.post(f"{self.base_url}{path}", json=body, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def get_faults(self, limit: int = 300, vin: Optional[str] = None):
        params = {"limit": limit}
        if vin:
            params["vin"] = vin
        data = self._get("/faults", params=params)
        return data if isinstance(data, list) else data.get("results", [])

    def post_oem_chat(self, query: str):
        try:
            return self._post("/oem_chat", {"query": query})
        except Exception as e:
            return {"answer": f"Error calling /oem_chat: {e}", "table": None}


client = BackendClient()

# ----------------------------
# Data transformers
# ----------------------------

def _severity_rank(sev: str) -> int:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return order.get((sev or "").lower(), -1)

def status_from_severity(sev: str) -> str:
    sev_l = (sev or "").lower()
    if sev_l == "critical": return "Critical"
    if sev_l == "high": return "Warning"
    if sev_l in ("medium", "low"): return "Warning"
    return "Healthy"

def normalize_faults(faults: List[Dict[str, Any]]) -> pd.DataFrame:
    if not faults:
        return pd.DataFrame()

    rows = []
    for item in faults:
        raw = item.get("raw_payload") or {}
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                raw = {}

        detected_at = pd.to_datetime(item.get("detected_at"), errors="coerce")
        odometer = raw.get("odometer_km")
        predicted = raw.get("predicted_failure_km") or item.get("predicted_failure_km")

        remaining = None
        if odometer is not None and predicted is not None:
            try:
                remaining = float(predicted) - float(odometer)
            except:
                remaining = None

        rows.append({
            "id": item.get("id"),
            "vin": item.get("vin"),
            "detected_at": detected_at,
            "component": item.get("component") or raw.get("component"),
            "severity": item.get("severity") or raw.get("severity"),
            "predicted_failure_km": predicted,
            "odometer_km": odometer,
            "remaining_km": remaining,
            "anomaly_reason": raw.get("anomaly_reason"),
            "coolant_temp_c": raw.get("coolant_temp_c"),
            "coolant_pressure_bar": raw.get("coolant_pressure_bar"),
            "engine_rpm": raw.get("engine_rpm"),
            "vibration_level": raw.get("vibration_level"),
            "battery_voltage": raw.get("battery_voltage"),
        })

    df = pd.DataFrame(rows)
    return df.sort_values("detected_at", ascending=False)

def build_vehicle_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["vin", "status", "active_component", "active_severity", "last_updated"])

    df["sev_rank"] = df["severity"].apply(_severity_rank)
    df_sorted = df.sort_values(["vin", "sev_rank", "detected_at"], ascending=[True, False, False])
    best = df_sorted.groupby("vin", as_index=False).first()

    return pd.DataFrame({
        "vin": best["vin"],
        "status": best["severity"].apply(status_from_severity),
        "active_component": best["component"],
        "active_severity": best["severity"],
        "last_updated": best["detected_at"],
    })

def compute_fleet_risk_score(df: pd.DataFrame) -> int:
    if df.empty:
        return 100
    high = (df["severity"].str.lower() == "high").sum()
    crit = (df["severity"].str.lower() == "critical").sum()
    score = 100 - (2 * high + 5 * crit)
    return max(0, score)
