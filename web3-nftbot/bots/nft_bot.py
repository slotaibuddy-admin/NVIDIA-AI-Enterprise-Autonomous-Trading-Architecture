"""
NFTBot — core NFT trading bot.

Coordinates the MarketAgent, RiskAgent, and PortfolioAgent to execute
standard NFT trades (buy / sell) on supported marketplaces.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.market_agent import MarketAgent
from agents.portfolio_agent import PortfolioAgent
from agents.risk_agent import RiskAgent

from .base_bot import BaseBot, BotStatus, TradeOrder

logger = logging.getLogger(__name__)


class NFTBot(BaseBot):
    """
    Core NFT trading bot.

    Flow per iteration
    ------------------
    1. Fetch market data for watched collections.
    2. Ask MarketAgent whether to BUY, SELL, or HOLD.
    3. Ask RiskAgent to approve/size the trade.
    4. Ask PortfolioAgent for any exit signals.
    5. Execute approved orders on-chain.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="NFTBot", config=config)
        self._market_agent = MarketAgent(config)
        self._risk_agent = RiskAgent(config)
        self._portfolio_agent = PortfolioAgent(config)
        self._poll_interval: float = config.get("bots", {}).get(
            "poll_interval_seconds", 30.0
        )
        self._watched_collections: list[str] = config.get("bots", {}).get(
            "watched_collections", []
        )

    # ------------------------------------------------------------------
    # BaseBot interface
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        logger.info("NFTBot: starting AI agents.")
        self._market_agent.start()
        self._risk_agent.start()
        self._portfolio_agent.start()
        logger.info("NFTBot: all agents ready.")

    def _disconnect(self) -> None:
        self._market_agent.stop()
        self._risk_agent.stop()
        self._portfolio_agent.stop()
        logger.info("NFTBot: agents stopped.")

    def _run_loop(self) -> None:
        logger.info(
            "NFTBot: entering trading loop (interval=%.1fs, collections=%s).",
            self._poll_interval,
            self._watched_collections,
        )
        while self.is_running:
            try:
                self._iteration()
            except Exception:
                logger.exception("NFTBot: unhandled error in iteration.")
                self._status = BotStatus.ERROR
                break
            time.sleep(self._poll_interval)

    def execute_order(self, order: TradeOrder) -> bool:
        """Submit *order* to the marketplace (stub implementation)."""
        logger.info(
            "NFTBot: executing %s order — collection=%s token=%s price=%.4f ETH on %s.",
            order.action,
            order.collection,
            order.token_id,
            order.price_eth,
            order.marketplace,
        )
        # Production: submit Web3 transaction here
        return True

    # ------------------------------------------------------------------
    # Core trading logic
    # ------------------------------------------------------------------

    def _iteration(self) -> None:
        """Run one full discover-analyse-decide-execute cycle."""
        for collection in self._watched_collections:
            market_data = self._fetch_market_data(collection)

            market_signal = self._market_agent.analyse(market_data)
            risk_signal = self._risk_agent.analyse(market_data)

            if market_signal.action == "HOLD":
                logger.debug("NFTBot: MarketAgent says HOLD for %s.", collection)
                continue

            if risk_signal.action == "SKIP":
                logger.info(
                    "NFTBot: RiskAgent rejected trade for %s (score=%s).",
                    collection,
                    risk_signal.metadata.get("risk_score"),
                )
                continue

            order = TradeOrder(
                bot_name=self.name,
                collection=collection,
                token_id="0",
                action=market_signal.action,
                price_eth=float(market_data.get("floor_price", 0.0)),
                marketplace=self.config.get("web3", {}).get(
                    "default_marketplace", "opensea"
                ),
            )
            self.execute_order(order)

        # Portfolio management
        portfolio_data = self._fetch_portfolio_data()
        portfolio_signal = self._portfolio_agent.analyse(portfolio_data)
        if portfolio_signal.action in ("EXIT", "REBALANCE"):
            logger.info(
                "NFTBot: PortfolioAgent triggered %s — %s.",
                portfolio_signal.action,
                portfolio_signal.metadata,
            )

    # ------------------------------------------------------------------
    # Data fetchers (stubs — replace with real marketplace API calls)
    # ------------------------------------------------------------------

    def _fetch_market_data(self, collection: str) -> dict[str, Any]:
        """Fetch current market data for *collection*."""
        return {
            "collection": collection,
            "floor_price": 0.5,
            "volume_24h": 100.0,
            "price_change_24h": 0.05,
            "sentiment_score": 0.6,
            "liquidity_score": 0.7,
            "volatility_30d": 0.3,
            "portfolio_value": 10.0,
            "proposed_trade_value": 0.5,
        }

    def _fetch_portfolio_data(self) -> dict[str, Any]:
        """Fetch current portfolio state."""
        return {
            "holdings": [],
            "target_weights": {},
            "stop_loss_pct": 0.20,
            "take_profit_pct": 0.50,
        }


if __name__ == "__main__":
    import yaml

    logging.basicConfig(level=logging.INFO)
    with open("config/config.yaml") as f:
        cfg = yaml.safe_load(f)
    bot = NFTBot(cfg)
    bot.start()
