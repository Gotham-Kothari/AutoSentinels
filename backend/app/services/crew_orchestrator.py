from __future__ import annotations
from langchain_anthropic import ChatAnthropic
import os
import platform
import signal
from datetime import datetime
from typing import Any, Dict

if platform.system() == "Windows":
    UNSUPPORTED_SIGNALS = [
        "SIGHUP",
        "SIGTSTP",
        "SIGQUIT",
        "SIGCONT",
        "SIGUSR1",
        "SIGUSR2",
        "SIGSTOP",
    ]

    for sig in UNSUPPORTED_SIGNALS:
        if not hasattr(signal, sig):
            setattr(signal, sig, signal.SIGTERM)



import anyio
from crewai import Agent, Task, Crew, Process, LLM

from app.config import settings
from app.logging_config import logger
from app.models.telemetry import TelemetryPayload
from app.models.faults import FaultRecord
from app.repositories.base import FaultRepository
from app.services.anomaly_detector import AnomalyResult
from app.utils.ids import generate_id


def _build_llm() -> LLM:
    """
    Default provider: Anthropic Claude 3.5 Sonnet.
    You can switch provider/model purely via .env / environment variables.
    """
    provider = (settings.llm_provider or "anthropic").lower()

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        return ChatAnthropic(
            model=settings.llm_model or "claude-3-haiku-20240307",
            anthropic_api_key=settings.anthropic_api_key,
            temperature=0.2,
            max_tokens=512,
        )

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment or .env")
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key

        logger.info("Using OpenAI provider with model=%s", settings.llm_model)
        return LLM(
            provider="openai",
            model=settings.llm_model or "gpt-4o",
            temperature=0.2,
            max_tokens=2048,
        )

    if provider == "groq":
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment or .env")
        os.environ["GROQ_API_KEY"] = settings.groq_api_key

        logger.info("Using Groq provider with model=%s", settings.llm_model)
        return LLM(
            provider="groq",
            model=settings.llm_model or "llama3-70b-8192",
            temperature=0.2,
            max_tokens=2048,
        )

    raise RuntimeError(f"Unsupported llm_provider: {settings.llm_provider}")


class CrewOrchestrator:
    """
    Orchestrates the multi-agent workflow using CrewAI.

    The rest of the backend talks to this class as a plain Python service:
    - It receives a validated TelemetryPayload and AnomalyResult.
    - It runs the multi-agent pipeline.
    - It persists a FaultRecord to the repository.
    - It returns a structured dict for API / dashboard usage.
    """

    def __init__(self, fault_repo: FaultRepository) -> None:
        self.fault_repo = fault_repo
        self.llm = _build_llm()
        self._init_agents()

    def _init_agents(self) -> None:
        """
        Instantiate agents once and reuse across requests.

        All agents share the same LLM configuration for performance and consistency.
        """

        self.data_agent = Agent(
            role="Data Monitoring Agent",
            goal=(
                "Summarize the critical aspects of incoming telemetry and any detected anomaly "
                "for downstream agents."
            ),
            backstory=(
                "You are an expert in automotive telematics and CAN bus data. "
                "You highlight only the most relevant parameters and risks."
            ),
            llm=self.llm,
        )

        self.diagnosis_agent = Agent(
            role="Diagnosis Agent",
            goal=(
                "Explain the likely failure mode, impacted component, and recommended urgency "
                "for a preventive service visit."
            ),
            backstory=(
                "You are a senior automotive diagnostic specialist who understands "
                "coolant systems, powertrain, and safety implications."
            ),
            llm=self.llm,
        )

        self.customer_agent = Agent(
            role="Customer Engagement Agent",
            goal=(
                "Draft a clear, reassuring message to the vehicle owner explaining the issue "
                "and proposing a preventive check."
            ),
            backstory=(
                "You are a courteous service advisor at a premium car brand. "
                "You avoid technical jargon and do not cause panic."
            ),
            llm=self.llm,
        )

        self.scheduling_agent = Agent(
            role="Scheduling Agent",
            goal=(
                "Convert customer consent into a precise service booking instruction that "
                "can be passed to the dealer or CRM system."
            ),
            backstory=(
                "You are a meticulous booking coordinator familiar with workshop calendars "
                "and peak load management."
            ),
            llm=self.llm,
        )

        self.insight_agent = Agent(
            role="OEM Insights Agent",
            goal=(
                "Summarize the incident for OEM R&D, including defect hypothesis and potential "
                "impact on reliability and safety across the fleet."
            ),
            backstory=(
                "You are a quality & reliability engineer who feeds structured insights into "
                "design improvement programs."
            ),
            llm=self.llm,
        )

    def _build_tasks(self, context: Dict[str, Any]) -> list[Task]:
        """
        Build CrewAI tasks for a given telemetry + anomaly context.

        Keeping the prompts narrow and deterministic ensures Anthropic outputs
        are predictable and safe to show in a live demo.
        """

        context_str = str(context)

        task1 = Task(
            description=(
                "You are given raw telemetry and an anomaly result. "
                "Using the following JSON context, summarize the key risk in 2–3 bullet points "
                "for technical stakeholders. Focus on the parameter deviations and why they matter.\n\n"
                f"Context: {context_str}"
            ),
            agent=self.data_agent,
            expected_output=(
                "2–3 bullet points summarizing the anomaly and its technical implications."
            ),
        )

        task2 = Task(
            description=(
                "Based on the same context, provide a diagnostic explanation:\n"
                "1) most probable failure mode,\n"
                "2) specific component affected,\n"
                "3) recommended urgency (low/medium/high/critical), and\n"
                "4) a one-line justification.\n\n"
                f"Context: {context_str}"
            ),
            agent=self.diagnosis_agent,
            expected_output=(
                "A short paragraph followed by a bullet list with failure mode, component, "
                "urgency, and justification."
            ),
        )

        task3 = Task(
            description=(
                "Draft a WhatsApp-style message to the vehicle owner explaining the situation "
                "in simple language and proposing a preventive service visit. "
                "Be calm, concise, and do not use technical jargon. "
                "Close with a question asking for a preferred day (e.g., 'Can I book you in on Tuesday?').\n\n"
                f"Context: {context_str}"
            ),
            agent=self.customer_agent,
            expected_output=(
                "A single message of 3–5 sentences that can be sent directly to the vehicle owner."
            ),
        )

        task4 = Task(
            description=(
                "Convert the situation into a precise service booking instruction for the dealer system. "
                "Assume the customer has agreed to a visit within the next 3 days. "
                "Respond ONLY with valid JSON, no extra text, using the fields:\n"
                "  preferred_date (YYYY-MM-DD),\n"
                "  preferred_time_window (e.g., '10:00-12:00'),\n"
                "  workshop_type (e.g., 'authorized_dealer'),\n"
                "  notes (short text).\n\n"
                f"Context: {context_str}"
            ),
            agent=self.scheduling_agent,
            expected_output=(
                "Strictly valid JSON object with the keys: preferred_date, preferred_time_window, "
                "workshop_type, notes."
            ),
        )

        task5 = Task(
            description=(
                "Write a concise technical summary for OEM R&D. Include:\n"
                "- VIN\n"
                "- component\n"
                "- severity\n"
                "- defect hypothesis\n"
                "- potential impact on safety and reliability across the fleet.\n"
                "Limit to 4–6 bullet points.\n\n"
                f"Context: {context_str}"
            ),
            agent=self.insight_agent,
            expected_output=(
                "4–6 bullet points that can be pasted into an OEM defect tracking system."
            ),
        )

        return [task1, task2, task3, task4, task5]

    async def run_pipeline(
        self,
        payload: TelemetryPayload,
        anomaly: AnomalyResult,
    ) -> Dict[str, Any]:
        """
        Run the full multi-agent pipeline for a given telemetry event.

        Returns:
            dict with:
              - context: normalized telemetry/anomaly context used for prompts
              - crew_output: raw string from CrewAI (good enough for demo)
              - fault_id: ID of the persisted fault record
        """

        context: Dict[str, Any] = {
            "vin": payload.vin,
            "timestamp": payload.timestamp.isoformat(),
            "coolant_temp_c": payload.coolant_temp_c,
            "coolant_pressure_bar": payload.coolant_pressure_bar,
            "engine_rpm": payload.engine_rpm,
            "vibration_level": payload.vibration_level,
            "battery_voltage": payload.battery_voltage,
            "odometer_km": payload.odometer_km,
            "anomaly_reason": getattr(anomaly, "reason", None),
            "predicted_failure_km": getattr(anomaly, "predicted_failure_km", None),
            "component": getattr(anomaly, "component", None),
            "severity": getattr(anomaly, "severity", None),
        }

        logger.info(
            "Running CrewAI pipeline for VIN=%s, component=%s, severity=%s",
            context["vin"],
            context["component"],
            context["severity"],
        )

        tasks = self._build_tasks(context)

        crew = Crew(
            agents=[
                self.data_agent,
                self.diagnosis_agent,
                self.customer_agent,
                self.scheduling_agent,
                self.insight_agent,
            ],
            tasks=tasks,
            process=Process.sequential,
        )

        # Run in a worker thread so we do not block the FastAPI event loop
        try:
            crew_result = await anyio.to_thread.run_sync(crew.kickoff)
        except Exception as exc:
            logger.exception("CrewAI pipeline failed: %s", exc)
            raise

        # Persist the fault record (non-blocking from API perspective)
        fault = FaultRecord(
            id=generate_id(),
            vin=payload.vin,
            detected_at=datetime.utcnow(),
            predicted_failure_km=anomaly.predicted_failure_km or 200.0,
            component=anomaly.component or "unknown",
            severity=anomaly.severity or "medium",
            raw_payload=context,
        )

        try:
            await self.fault_repo.save_fault(fault)
        except Exception as exc:
            # Do not kill the request if persistence fails; just log it.
            logger.exception("Failed to persist fault record: %s", exc)

        return {
            "context": context,
            "crew_output": str(crew_result),
            "fault_id": fault.id,
        }
