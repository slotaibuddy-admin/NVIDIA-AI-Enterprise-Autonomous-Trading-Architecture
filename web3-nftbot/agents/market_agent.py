"""
MarketAgent — GPU-accelerated price prediction and trend analysis agent.

Uses an NVIDIA-accelerated inference model to score NFT collection
opportunities based on price history, volume, and social sentiment.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_agent import AgentSignal, BaseAgent

logger = logging.getLogger(__name__)


class MarketAgent(BaseAgent):
    """
    Analyses NFT market data and predicts short-term price movements.

    Signals
    -------
    - **BUY**  — positive momentum, floor likely to rise
    - **SELL** — negative momentum, floor likely to fall
    - **HOLD** — insufficient signal strength
    """

    # Confidence threshold below which the agent emits HOLD
    _HOLD_THRESHOLD = 0.55

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="MarketAgent", config=config)
        self._model: Any = None

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Initialise the inference model (stub — replace with real model)."""
        model_path = self.config.get("agents", {}).get(
            "market_model_path", "models/market_predictor.onnx"
        )
        logger.info("MarketAgent: loading model from '%s'.", model_path)
        # Production: load ONNX / TensorRT model here
        self._model = _StubMarketModel()
        logger.info("MarketAgent: model loaded successfully.")

    def analyse(self, market_data: dict[str, Any]) -> AgentSignal:
        """
        Score the provided *market_data* and return a trading signal.

        Parameters
        ----------
        market_data:
            Expected keys: ``floor_price``, ``volume_24h``,
            ``price_change_24h``, ``sentiment_score``.
        """
        if not self.is_ready:
            raise RuntimeError("MarketAgent is not started. Call start() first.")

        score = self._model.predict(market_data)
        action, confidence = self._score_to_signal(score)

        signal = AgentSignal(
            agent_name=self.name,
            action=action,
            confidence=confidence,
            metadata={
                "raw_score": score,
                "floor_price": market_data.get("floor_price"),
                "volume_24h": market_data.get("volume_24h"),
            },
        )
        logger.debug("MarketAgent signal: %s", signal)
        return signal

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _score_to_signal(self, score: float) -> tuple[str, float]:
        """
        Map a raw model score in [-1, 1] to an (action, confidence) pair.

        Score > 0  → bullish → BUY
        Score < 0  → bearish → SELL
        |Score| < threshold → HOLD
        """
        confidence = abs(score)
        if confidence < self._HOLD_THRESHOLD:
            return "HOLD", confidence
        return ("BUY" if score > 0 else "SELL"), confidence


# ---------------------------------------------------------------------------
# Stub model (replaced by real ONNX/TensorRT model in production)
# ---------------------------------------------------------------------------


class _StubMarketModel:
    """Placeholder model that returns a neutral score for testing."""

    def predict(self, market_data: dict[str, Any]) -> float:
        """
        Return a score in [-1.0, 1.0].

        Production: run GPU inference here.
        """
        price_change = float(market_data.get("price_change_24h", 0.0))
        sentiment = float(market_data.get("sentiment_score", 0.0))
        # Simple weighted combination for demonstration
        return 0.6 * price_change + 0.4 * sentiment
