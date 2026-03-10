"""Base agent — abstract contract that all NFTflow agents must implement."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AgentSignal:
    """Structured output produced by an agent after analysing market data."""

    agent_name: str
    action: str                    # e.g. "BUY", "SELL", "HOLD", "SKIP"
    confidence: float              # 0.0 – 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )


class BaseAgent(ABC):
    """
    Abstract base class for all NFTflow AI agents.

    Subclasses must implement :meth:`analyse` to produce an
    :class:`AgentSignal` from raw market data.
    """

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self._ready = False
        logger.info("Agent '%s' initialised.", self.name)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Load models and warm up the agent."""
        self._load_model()
        self._ready = True
        logger.info("Agent '%s' started and ready.", self.name)

    def stop(self) -> None:
        """Release resources held by the agent."""
        self._ready = False
        logger.info("Agent '%s' stopped.", self.name)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _load_model(self) -> None:
        """Load the underlying AI model (GPU or CPU)."""

    @abstractmethod
    def analyse(self, market_data: dict[str, Any]) -> AgentSignal:
        """
        Analyse *market_data* and return a trading signal.

        Parameters
        ----------
        market_data:
            Dictionary containing relevant NFT market information such as
            floor price, volume, listing activity, and sentiment scores.

        Returns
        -------
        AgentSignal
            The agent's recommendation with a confidence score.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        """Return ``True`` if the agent has been started successfully."""
        return self._ready

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, ready={self._ready})"
