"""
PortfolioAgent — NFT portfolio management and rebalancing agent.

Tracks current holdings, calculates P&L, and determines whether the
portfolio needs rebalancing based on target allocation weights.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import AgentSignal, BaseAgent

logger = logging.getLogger(__name__)

# Number of decimal places used when rounding P&L percentages in metadata
_PNL_ROUNDING_DECIMALS = 4


class PortfolioAgent(BaseAgent):
    """
    Monitors the NFT portfolio and triggers rebalancing when drift
    exceeds the configured threshold.

    Signals
    -------
    - **REBALANCE** — portfolio has drifted; adjust holdings
    - **HOLD**      — portfolio is within target weights
    - **EXIT**      — a position has hit its stop-loss or profit target
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="PortfolioAgent", config=config)
        self._drift_threshold: float = config.get("agents", {}).get(
            "portfolio_drift_threshold", 0.10
        )

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """PortfolioAgent uses rule-based logic — no model file required."""
        logger.info("PortfolioAgent: portfolio engine initialised.")

    def analyse(self, market_data: dict[str, Any]) -> AgentSignal:
        """
        Evaluate the current portfolio state and return a management signal.

        Parameters
        ----------
        market_data:
            Expected keys: ``holdings`` (list of position dicts with keys
            ``collection``, ``quantity``, ``current_value``, ``cost_basis``),
            ``target_weights`` (dict mapping collection → target weight 0–1),
            ``stop_loss_pct``, ``take_profit_pct``.
        """
        if not self.is_ready:
            raise RuntimeError(
                "PortfolioAgent is not started. Call start() first."
            )

        holdings: list[dict[str, Any]] = market_data.get("holdings", [])
        target_weights: dict[str, float] = market_data.get("target_weights", {})

        # Check stop-loss / take-profit exits first
        exits = self._check_exits(holdings, market_data)
        if exits:
            return AgentSignal(
                agent_name=self.name,
                action="EXIT",
                confidence=1.0,
                metadata={"exit_positions": exits},
            )

        # Compute portfolio drift
        drift = self._compute_drift(holdings, target_weights)
        if drift > self._drift_threshold:
            return AgentSignal(
                agent_name=self.name,
                action="REBALANCE",
                confidence=min(1.0, drift / self._drift_threshold),
                metadata={
                    "drift": drift,
                    "threshold": self._drift_threshold,
                    "pnl_summary": self._compute_pnl(holdings),
                },
            )

        return AgentSignal(
            agent_name=self.name,
            action="HOLD",
            confidence=1.0 - drift,
            metadata={"pnl_summary": self._compute_pnl(holdings)},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_exits(
        self,
        holdings: list[dict[str, Any]],
        market_data: dict[str, Any],
    ) -> list[str]:
        """Return the list of collections that have hit an exit condition."""
        stop_loss_pct: float = float(market_data.get("stop_loss_pct", 0.20))
        take_profit_pct: float = float(market_data.get("take_profit_pct", 0.50))
        exits: list[str] = []

        for position in holdings:
            cost = float(position.get("cost_basis", 0.0))
            if cost == 0:
                continue
            current = float(position.get("current_value", 0.0))
            pnl_pct = (current - cost) / cost

            if pnl_pct <= -stop_loss_pct or pnl_pct >= take_profit_pct:
                exits.append(position["collection"])

        return exits

    def _compute_drift(
        self,
        holdings: list[dict[str, Any]],
        target_weights: dict[str, float],
    ) -> float:
        """
        Return the maximum absolute drift between actual and target weights.
        Returns 0.0 when no target weights are defined.
        """
        if not target_weights or not holdings:
            return 0.0

        total_value = sum(float(p.get("current_value", 0.0)) for p in holdings)
        if total_value == 0:
            return 0.0

        actual_weights: dict[str, float] = {
            p["collection"]: float(p.get("current_value", 0.0)) / total_value
            for p in holdings
        }

        drift = 0.0
        for collection, target in target_weights.items():
            actual = actual_weights.get(collection, 0.0)
            drift = max(drift, abs(actual - target))

        return drift

    def _compute_pnl(self, holdings: list[dict[str, Any]]) -> dict[str, float]:
        """Return a summary dict with total cost, value, and P&L."""
        total_cost = sum(float(p.get("cost_basis", 0.0)) for p in holdings)
        total_value = sum(float(p.get("current_value", 0.0)) for p in holdings)
        pnl = total_value - total_cost
        pnl_pct = (pnl / total_cost) if total_cost > 0 else 0.0
        return {
            "total_cost": total_cost,
            "total_value": total_value,
            "pnl": pnl,
            "pnl_pct": round(pnl_pct, _PNL_ROUNDING_DECIMALS),
        }
