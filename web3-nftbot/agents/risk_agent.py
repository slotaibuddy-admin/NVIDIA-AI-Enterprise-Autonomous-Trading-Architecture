"""
RiskAgent — position sizing and risk management agent.

Scores each trade opportunity on a 1–10 risk scale and determines
the maximum safe trade size relative to the current portfolio value.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import AgentSignal, BaseAgent

logger = logging.getLogger(__name__)

# Risk score boundaries (1 = lowest risk, 10 = highest risk)
_MIN_RISK = 1
_MAX_RISK = 10

# Trades with a risk score above this threshold are skipped
_RISK_CUTOFF = 7


class RiskAgent(BaseAgent):
    """
    Evaluates the risk of a proposed trade and recommends position sizing.

    Signals
    -------
    - **PROCEED** — trade is within acceptable risk limits
    - **REDUCE**  — trade is risky; reduce position size
    - **SKIP**    — trade exceeds maximum risk threshold
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="RiskAgent", config=config)
        self._max_portfolio_pct: float = config.get("bots", {}).get(
            "max_trade_pct_portfolio", 0.05
        )

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """RiskAgent uses rule-based logic — no model file required."""
        logger.info("RiskAgent: rule-based engine initialised.")

    def analyse(self, market_data: dict[str, Any]) -> AgentSignal:
        """
        Assess risk for the given *market_data* and return a signal.

        Parameters
        ----------
        market_data:
            Expected keys: ``floor_price``, ``liquidity_score``,
            ``volatility_30d``, ``portfolio_value``, ``proposed_trade_value``.
        """
        if not self.is_ready:
            raise RuntimeError("RiskAgent is not started. Call start() first.")

        risk_score = self._compute_risk_score(market_data)
        action, confidence = self._risk_score_to_signal(risk_score)

        max_trade = self._compute_max_trade_size(
            portfolio_value=float(market_data.get("portfolio_value", 0.0)),
            risk_score=risk_score,
        )

        signal = AgentSignal(
            agent_name=self.name,
            action=action,
            confidence=confidence,
            metadata={
                "risk_score": risk_score,
                "max_trade_size_eth": max_trade,
                "risk_cutoff": _RISK_CUTOFF,
            },
        )
        logger.debug("RiskAgent signal: %s", signal)
        return signal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_risk_score(self, market_data: dict[str, Any]) -> int:
        """
        Compute an integer risk score in [1, 10].

        Higher volatility and lower liquidity increase the risk score.
        """
        volatility = float(market_data.get("volatility_30d", 0.0))
        liquidity = float(market_data.get("liquidity_score", 1.0))

        # Normalise volatility to [0, 5] and invert liquidity to [0, 5]
        vol_component = min(volatility * 5.0, 5.0)
        liq_component = max(0.0, 5.0 - liquidity * 5.0)

        raw = vol_component + liq_component
        return max(_MIN_RISK, min(_MAX_RISK, round(raw)))

    def _risk_score_to_signal(self, risk_score: int) -> tuple[str, float]:
        if risk_score > _RISK_CUTOFF:
            confidence = min(1.0, (risk_score - _RISK_CUTOFF) / (_MAX_RISK - _RISK_CUTOFF))
            return "SKIP", confidence
        if risk_score >= _RISK_CUTOFF - 1:
            return "REDUCE", 0.6
        confidence = 1.0 - (risk_score - _MIN_RISK) / (_MAX_RISK - _MIN_RISK)
        return "PROCEED", max(0.5, confidence)

    def _compute_max_trade_size(
        self, portfolio_value: float, risk_score: int
    ) -> float:
        """Return the maximum recommended trade size in ETH."""
        # Scale down max trade size as risk increases
        risk_factor = 1.0 - (risk_score - _MIN_RISK) / (_MAX_RISK - _MIN_RISK)
        return portfolio_value * self._max_portfolio_pct * risk_factor
