from abc import ABC, abstractmethod
from typing import List
from app.models.faults import FaultRecord


class FaultRepository(ABC):
    @abstractmethod
    async def save_fault(self, fault: FaultRecord) -> None:
        ...

    @abstractmethod
    async def list_faults_for_vin(self, vin: str) -> List[FaultRecord]:
        ...

    @abstractmethod
    async def list_recent_faults(self, limit: int = 50) -> List[FaultRecord]:
        ...
