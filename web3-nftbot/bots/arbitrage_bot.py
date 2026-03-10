"""
ArbitrageBot — cross-marketplace NFT arbitrage bot.

Detects price differences for the same token across multiple NFT
marketplaces and executes simultaneous buy/sell orders to lock in profit.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.risk_agent import RiskAgent

from .base_bot import BaseBot, BotStatus, TradeOrder

logger = logging.getLogger(__name__)

# Minimum net profit in ETH after gas fees to execute an arbitrage trade
_MIN_PROFIT_ETH = 0.01


class ArbitrageBot(BaseBot):
    """
    Cross-marketplace arbitrage bot for NFTs.

    For each watched collection the bot queries all configured marketplaces,
    identifies the cheapest ask and the highest bid across venues, and
    executes a buy-low / sell-high pair when the spread exceeds the minimum
    profit threshold (accounting for estimated gas costs).
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="ArbitrageBot", config=config)
        arb_cfg = config.get("bots", {}).get("arbitrage", {})
        self._min_profit_eth: float = arb_cfg.get(
            "min_profit_eth", _MIN_PROFIT_ETH
        )
        self._gas_estimate_eth: float = arb_cfg.get("gas_estimate_eth", 0.005)
        self._marketplaces: list[str] = arb_cfg.get(
            "marketplaces", ["opensea", "blur", "looksrare"]
        )
        self._poll_interval: float = arb_cfg.get("poll_interval_seconds", 10.0)
        self._watched_collections: list[str] = config.get("bots", {}).get(
            "watched_collections", []
        )
        self._risk_agent = RiskAgent(config)

    # ------------------------------------------------------------------
    # BaseBot interface
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        logger.info("ArbitrageBot: starting risk agent.")
        self._risk_agent.start()
        logger.info(
            "ArbitrageBot: monitoring %d marketplaces.",
            len(self._marketplaces),
        )

    def _disconnect(self) -> None:
        self._risk_agent.stop()
        logger.info("ArbitrageBot: disconnected.")

    def _run_loop(self) -> None:
        logger.info(
            "ArbitrageBot: entering arbitrage loop (interval=%.1fs).",
            self._poll_interval,
        )
        while self.is_running:
            try:
                self._scan_for_arbitrage()
            except Exception:
                logger.exception("ArbitrageBot: unhandled error in scan.")
                self._status = BotStatus.ERROR
                break
            time.sleep(self._poll_interval)

    def execute_order(self, order: TradeOrder) -> bool:
        """Submit *order* to the marketplace (stub implementation)."""
        logger.info(
            "ArbitrageBot: ⚡ %s — collection=%s token=%s price=%.4f ETH on %s.",
            order.action,
            order.collection,
            order.token_id,
            order.price_eth,
            order.marketplace,
        )
        # Production: submit Web3 transaction here
        return True

    # ------------------------------------------------------------------
    # Core arbitrage logic
    # ------------------------------------------------------------------

    def _scan_for_arbitrage(self) -> None:
        """Scan all collections for cross-marketplace arbitrage opportunities."""
        for collection in self._watched_collections:
            prices = self._fetch_prices_across_markets(collection)
            opportunity = self._find_best_opportunity(prices)
            if opportunity is None:
                continue

            buy_marketplace, token_id, buy_price, sell_marketplace, sell_price = (
                opportunity
            )
            net_profit = sell_price - buy_price - self._gas_estimate_eth

            if net_profit < self._min_profit_eth:
                logger.debug(
                    "ArbitrageBot: spread too small for %s (profit=%.4f ETH).",
                    collection,
                    net_profit,
                )
                continue

            market_data = self._build_market_data(collection, buy_price)
            risk_signal = self._risk_agent.analyse(market_data)
            if risk_signal.action == "SKIP":
                logger.info(
                    "ArbitrageBot: risk agent rejected arb for %s.", collection
                )
                continue

            logger.info(
                "ArbitrageBot: ⚡ arbitrage found — buy on %s @ %.4f ETH, "
                "sell on %s @ %.4f ETH, net profit=%.4f ETH.",
                buy_marketplace,
                buy_price,
                sell_marketplace,
                sell_price,
                net_profit,
            )

            buy_order = TradeOrder(
                bot_name=self.name,
                collection=collection,
                token_id=token_id,
                action="BUY",
                price_eth=buy_price,
                marketplace=buy_marketplace,
                metadata={"arb_pair": sell_marketplace},
            )
            sell_order = TradeOrder(
                bot_name=self.name,
                collection=collection,
                token_id=token_id,
                action="SELL",
                price_eth=sell_price,
                marketplace=sell_marketplace,
                metadata={"arb_pair": buy_marketplace},
            )
            self.execute_order(buy_order)
            self.execute_order(sell_order)

    def _find_best_opportunity(
        self, prices: dict[str, dict[str, float]]
    ) -> tuple[str, str, float, str, float] | None:
        """
        Find the best buy/sell pair across marketplaces.

        Returns
        -------
        tuple(buy_market, token_id, buy_price, sell_market, sell_price) or None
        """
        best: tuple[str, str, float, str, float] | None = None
        best_spread = 0.0

        for token_id, market_prices in prices.items():
            if len(market_prices) < 2:
                continue
            sorted_markets = sorted(market_prices.items(), key=lambda x: x[1])
            cheapest_market, cheapest_price = sorted_markets[0]
            priciest_market, priciest_price = sorted_markets[-1]
            spread = priciest_price - cheapest_price
            if spread > best_spread:
                best_spread = spread
                best = (
                    cheapest_market,
                    token_id,
                    cheapest_price,
                    priciest_market,
                    priciest_price,
                )

        return best

    # ------------------------------------------------------------------
    # Data fetchers (stubs — replace with real marketplace API calls)
    # ------------------------------------------------------------------

    def _fetch_prices_across_markets(
        self, collection: str
    ) -> dict[str, dict[str, float]]:
        """
        Return a nested dict: {token_id: {marketplace: price_eth}}.
        Stub returns an empty dict.
        """
        return {}

    def _build_market_data(
        self, collection: str, price_eth: float
    ) -> dict[str, Any]:
        return {
            "collection": collection,
            "floor_price": price_eth,
            "volume_24h": 200.0,
            "price_change_24h": 0.0,
            "sentiment_score": 0.5,
            "liquidity_score": 0.8,
            "volatility_30d": 0.2,
            "portfolio_value": 10.0,
            "proposed_trade_value": price_eth,
        }


if __name__ == "__main__":
    import yaml

    logging.basicConfig(level=logging.INFO)
    with open("config/config.yaml") as f:
        cfg = yaml.safe_load(f)
    bot = ArbitrageBot(cfg)
    bot.start()
