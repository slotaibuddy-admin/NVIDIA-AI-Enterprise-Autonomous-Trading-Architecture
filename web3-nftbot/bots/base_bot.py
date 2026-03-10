"""Base bot — abstract contract that all NFTflow bots must implement."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class BotStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class TradeOrder:
    """Represents a single buy or sell order to be submitted on-chain."""

    bot_name: str
    collection: str
    token_id: str
    action: str          # "BUY" | "SELL"
    price_eth: float
    marketplace: str     # e.g. "opensea", "blur", "looksrare"
    metadata: dict[str, Any] | None = None


class BaseBot(ABC):
    """
    Abstract base class for all NFTflow trading bots.

    Bots are responsible for interacting with Web3 marketplaces.
    All AI decision-making is delegated to agents.
    """

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        self.name = name
        self.config = config
        self._status = BotStatus.IDLE
        logger.info("Bot '%s' initialised.", self.name)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Connect to Web3 endpoints and begin the trading loop."""
        self._connect()
        self._status = BotStatus.RUNNING
        logger.info("Bot '%s' started.", self.name)
        self._run_loop()

    def pause(self) -> None:
        """Temporarily pause trading without disconnecting."""
        self._status = BotStatus.PAUSED
        logger.info("Bot '%s' paused.", self.name)

    def stop(self) -> None:
        """Gracefully stop the bot and release resources."""
        self._status = BotStatus.STOPPED
        self._disconnect()
        logger.info("Bot '%s' stopped.", self.name)

    # ------------------------------------------------------------------
    # Interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _connect(self) -> None:
        """Establish Web3 connection and authenticate wallet."""

    @abstractmethod
    def _disconnect(self) -> None:
        """Close Web3 connection."""

    @abstractmethod
    def _run_loop(self) -> None:
        """Main event/poll loop — implemented by each bot subclass."""

    @abstractmethod
    def execute_order(self, order: TradeOrder) -> bool:
        """
        Submit *order* to the blockchain marketplace.

        Returns
        -------
        bool
            ``True`` if the transaction was accepted, ``False`` otherwise.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def status(self) -> BotStatus:
        return self._status

    @property
    def is_running(self) -> bool:
        return self._status == BotStatus.RUNNING

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, status={self._status.value})"
