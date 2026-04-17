from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class BaseAgent(ABC):
    name: str
    description: str

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    async def stream(self, context: dict[str, Any]) -> AsyncIterator[str]:
        if False:
            yield ''
