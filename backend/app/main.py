import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from typing import List

from app.logging_config import logger
from app.config import settings
from app.models.telemetry import TelemetryPayload
from app.models.faults import FaultRecord
from app.services.anomaly_detector import AnomalyDetector
from app.services.crew_orchestrator import CrewOrchestrator, _build_llm
from app.repositories.sqlite_repo import SQLiteFaultRepository, init_db
from app.repositories.base import FaultRepository
from app.repositories.sqlite_repo import get_fault_repo
import logging

from pydantic import BaseModel
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title=settings.app_name)

# CORS — so Streamlit etc. can talk to this
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection – repository + orchestrator
async def get_fault_repo():
    return SQLiteFaultRepository()


async def get_orchestrator(
    repo: SQLiteFaultRepository = Depends(get_fault_repo),
) -> CrewOrchestrator:
    return CrewOrchestrator(fault_repo=repo)


@app.on_event("startup")
async def on_startup():
    logger.info("Starting up AutoSentinels backend...")
    await init_db()
    logger.info("Database initialized.")


@app.get("/health", tags=["meta"])
async def health_check():
    return {"status": "ok", "environment": settings.environment}


@app.post("/telematics/ingest", tags=["telematics"])
async def ingest_telemetry(
    payload: TelemetryPayload,
    orchestrator: CrewOrchestrator = Depends(get_orchestrator),
):
    """
    Main entrypoint for sensor data.
    - Validates payload.
    - Runs anomaly detection.
    - If anomaly: triggers CrewAI in background-style flow and returns case id.
    """

    logger.info("Received telemetry for VIN=%s", payload.vin)

    # Anomaly detection
    anomaly = await AnomalyDetector.detect(payload)

    if not anomaly.is_anomaly:
        return {
            "status": "ok",
            "anomaly": False,
            "message": "No anomaly detected.",
        }

    try:
        result = await orchestrator.run_pipeline(payload, anomaly)
    except Exception as e:
        logger.exception("Failed to run orchestrator: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal processing error; please try again later.",
        )

    return {
        "status": "anomaly_detected",
        "anomaly": True,
        "fault_id": result["fault_id"],
        "summary": result["context"],
        "crew_output": result["crew_output"],
    }




@app.get("/faults", response_model=List[FaultRecord], tags=["faults"])
async def list_recent_faults(
    limit: int = 50,
    repo: SQLiteFaultRepository = Depends(get_fault_repo),
):
    try:
        return await repo.list_recent_faults(limit=limit)
    except Exception as e:
        logger.exception("Error fetching recent faults: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch faults.",
        )

logger = logging.getLogger("autosentinels")


class ChatRequest(BaseModel):
    vin: str
    message: str


class ChatResponse(BaseModel):
    vin: str
    user_message: str
    bot_message: str
    severity: Optional[str] = None
    component: Optional[str] = None
    predicted_failure_km: Optional[float] = None
    anomaly_reason: Optional[str] = None

# ================================================================
# OEM Chat models (MUST be defined before the /oem_chat endpoint)
# ================================================================

class OemChatRow(BaseModel):
    vin: str
    component: Optional[str] = None
    severity: Optional[str] = None
    remaining_km: Optional[float] = None

class OemChatRequest(BaseModel):
    query: str

class OemChatResponse(BaseModel):
    answer: str
    table: Optional[List[OemChatRow]] = None


@app.post("/oem_chat", response_model = OemChatResponse)
async def oem_chat_endpoint(
    payload: OemChatRequest,
    repo: FaultRepository = Depends(get_fault_repo),
):
    """
    OEM-facing chat endpoint.

    - Takes a free-form query about the fleet.
    - Builds a compact fleet snapshot from recent faults.
    - Sends everything to the LLM via _build_llm().
    - Returns answer + a tabular view of the underlying data.
    """
    user_query = (payload.query or "").strip()
    logger.info("OEM_CHAT_DEBUG: Received /oem_chat query=%s", user_query)

    # ----------------------------
    # LOAD FLEET CONTEXT
    # ----------------------------
    try:
        faults = await repo.list_recent_faults(limit=300)
        logger.info("OEM_CHAT_DEBUG: Retrieved %d recent faults", len(faults))
    except Exception as e:
        logger.exception("OEM_CHAT_DEBUG: Error fetching faults: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch fleet faults for OEM chat.",
        )

    # Build tabular context (and remaining_km) for response + prompt
    table_rows: List[OemChatRow] = []
    fleet_lines = []

    for f in faults:
        raw = f.raw_payload
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                logger.error("OEM_CHAT_DEBUG: JSON decode failed for raw_payload string")
                raw = {}

        component = raw.get("component", f.component)
        severity = raw.get("severity", f.severity)
        odometer = raw.get("odometer_km")
        predicted_km = raw.get("predicted_failure_km", f.predicted_failure_km)

        remaining_km = None
        if odometer is not None and predicted_km is not None:
            try:
                remaining_km = float(predicted_km) - float(odometer)
            except Exception:
                remaining_km = None

        row = OemChatRow(
            vin=f.vin,
            component=component,
            severity=severity,
            remaining_km=remaining_km,
        )
        table_rows.append(row)

        # Keep LLM context compact: one line per VIN/fault
        fleet_lines.append(
            f"VIN={f.vin} | component={component} | severity={severity} | "
            f"remaining_km={remaining_km}"
        )

    # ----------------------------
    # BUILD LLM MESSAGES
    # ----------------------------
    try:
        snapshot_text = "\n".join(fleet_lines[:80])  # cap to avoid huge prompts

        messages = [
            SystemMessage(
                content=(
                    "You are the AutoSentinels OEM Agent Brain. "
                    "You answer questions for OEM reliability / quality teams using "
                    "ONLY the fleet snapshot provided. "
                    "Be specific about which VINs/components are at risk, "
                    "timeframes (in km / weeks) and recommended actions."
                )
            ),
            HumanMessage(
                content=f"""
Fleet snapshot (recent faults, one per line):
{snapshot_text}

OEM question:
{user_query}

Respond in 2–4 short paragraphs, then optionally a bullet list of key actions.
"""
            ),
        ]
        logger.info("OEM_CHAT_DEBUG: Messages for LLM constructed.")
    except Exception as e:
        logger.exception("OEM_CHAT_DEBUG: Error constructing messages: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while preparing OEM chat prompt.",
        )

    # ----------------------------
    # CALL LLM
    # ----------------------------
    try:
        llm = _build_llm()
        logger.info("OEM_CHAT_DEBUG: LLM built successfully: %s", llm)
        response = llm.invoke(messages)
        logger.info("OEM_CHAT_DEBUG: LLM raw response: %s", response)
        answer_text = response.content.strip()
    except Exception as e:
        logger.exception("OEM_CHAT_DEBUG: LLM error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {str(e)}",
        )

    # ----------------------------
    # RETURN OEM CHAT RESPONSE
    # ----------------------------
    return OemChatResponse(
        answer=answer_text,
        table=table_rows if table_rows else None,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    repo: FaultRepository = Depends(get_fault_repo),
):
    vin = payload.vin.strip()
    user_msg = payload.message.strip()

    logger.info("CHAT_DEBUG: Received /chat request | vin=%s | message=%s", vin, user_msg)

    try:
        faults = await repo.list_faults_for_vin(vin)
        logger.info("CHAT_DEBUG: Retrieved faults: %s", faults)
    except Exception as e:
        logger.error("CHAT_DEBUG: Error retrieving faults: %s", e)
        raise

    # ----------------------------
    # BUILD FAULT CONTEXT
    # ----------------------------
    try:
        if faults:
            f = faults[0]
            raw = f.raw_payload
            logger.info("CHAT_DEBUG: Raw payload before normalization: %s", raw)

            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    logger.error("CHAT_DEBUG: JSON decode failed for raw_payload string")
                    raw = {}

            component = raw.get("component", f.component)
            severity = raw.get("severity", f.severity)
            reason = raw.get("anomaly_reason", "An anomaly was detected.")
            predicted_km = raw.get("predicted_failure_km", f.predicted_failure_km)

            fault_context = f"""
Detected Fault:
- Component: {component}
- Severity: {severity}
- Reason: {reason}
- Predicted failure distance: approx. {predicted_km} km
"""
        else:
            fault_context = "No active faults detected."

        logger.info("CHAT_DEBUG: Fault context built: %s", fault_context.replace("\n", " | "))
    except Exception as e:
        logger.error("CHAT_DEBUG: Error building fault context: %s", e)
        raise

    # ----------------------------
    # BUILD CHAT MESSAGE
    # ----------------------------
    try:
        messages = [
            SystemMessage(
                content=(
                    "You are AutoSentinels. Only answer using the provided fault context."
                )
            ),
            HumanMessage(
                content=f"""
Vehicle VIN: {vin}

{fault_context}

Driver Question: "{user_msg}"
"""
            )
        ]

        logger.info("CHAT_DEBUG: Messages constructed successfully.")
    except Exception as e:
        logger.error("CHAT_DEBUG: Error constructing messages: %s", e)
        raise

    # ----------------------------
    # CALL LLM
    # ----------------------------
    try:
        llm = _build_llm()
        logger.info("CHAT_DEBUG: LLM built successfully: %s", llm)

        response = llm.invoke(messages)
        logger.info("CHAT_DEBUG: LLM raw response: %s", response)

        reply_text = response.content.strip()
        logger.info("CHAT_DEBUG: LLM reply_text extracted: %s", reply_text)
    except Exception as e:
        logger.error("CHAT_DEBUG: LLM error: %s", e)
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    # ----------------------------
    # RETURN CHAT RESPONSE
    # ----------------------------
    try:
        resp = ChatResponse(
            vin=vin,
            user_message=user_msg,
            bot_message=reply_text,
            severity=severity if faults else None,
            component=component if faults else None,
            predicted_failure_km=predicted_km if faults else None,
            anomaly_reason=reason if faults else None,
        )
        logger.info("CHAT_DEBUG: ChatResponse constructed successfully: %s", resp)
        return resp

    except Exception as e:
        logger.error("CHAT_DEBUG: Error constructing ChatResponse: %s", e)
        raise