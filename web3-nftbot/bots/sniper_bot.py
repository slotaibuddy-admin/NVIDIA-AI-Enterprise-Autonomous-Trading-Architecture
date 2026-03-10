"""
SniperBot — ultra-fast NFT floor and rarity hunting bot.

Monitors new listings and immediately purchases NFTs that are priced
below floor or belong to a rare trait tier, before other buyers can react.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.market_agent import MarketAgent
from agents.risk_agent import RiskAgent

from .base_bot import BaseBot, BotStatus, TradeOrder

logger = logging.getLogger(__name__)


class SniperBot(BaseBot):
    """
    NFT sniper bot that targets underpriced and rare listings.

    Snipe conditions
    ----------------
    - Listing price is at least *floor_discount_pct* below the current floor.
    - OR the token's rarity rank falls within the top *rarity_top_pct* percent
      of the collection and is listed below the rarity-adjusted price.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(name="SniperBot", config=config)
        sniper_cfg = config.get("bots", {}).get("sniper", {})
        self._floor_discount_pct: float = sniper_cfg.get("floor_discount_pct", 0.05)
        self._rarity_top_pct: float = sniper_cfg.get("rarity_top_pct", 0.10)
        self._max_price_eth: float = sniper_cfg.get("max_price_eth", 1.0)
        self._poll_interval: float = sniper_cfg.get("poll_interval_seconds", 5.0)
        self._watched_collections: list[str] = config.get("bots", {}).get(
            "watched_collections", []
        )
        self._market_agent = MarketAgent(config)
        self._risk_agent = RiskAgent(config)

    # ------------------------------------------------------------------
    # BaseBot interface
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        logger.info("SniperBot: starting agents.")
        self._market_agent.start()
        self._risk_agent.start()
        logger.info("SniperBot: ready to snipe.")

    def _disconnect(self) -> None:
        self._market_agent.stop()
        self._risk_agent.stop()
        logger.info("SniperBot: agents stopped.")

    def _run_loop(self) -> None:
        logger.info(
            "SniperBot: entering sniper loop (interval=%.1fs).",
            self._poll_interval,
        )
        while self.is_running:
            try:
                self._scan_for_targets()
            except Exception:
                logger.exception("SniperBot: unhandled error in scan.")
                self._status = BotStatus.ERROR
                break
            time.sleep(self._poll_interval)

    def execute_order(self, order: TradeOrder) -> bool:
        """Submit a snipe order to the marketplace (stub implementation)."""
        logger.info(
            "SniperBot: 🎯 SNIPING — collection=%s token=%s price=%.4f ETH.",
            order.collection,
            order.token_id,
            order.price_eth,
        )
        # Production: submit Web3 transaction here with aggressive gas settings
        return True

    # ------------------------------------------------------------------
    # Core sniper logic
    # ------------------------------------------------------------------

    def _scan_for_targets(self) -> None:
        """Scan all watched collections for snipe-worthy listings."""
        for collection in self._watched_collections:
            listings = self._fetch_new_listings(collection)
            floor_price = self._fetch_floor_price(collection)

            for listing in listings:
                if self._is_snipe_target(listing, floor_price):
                    market_data = self._build_market_data(listing, floor_price)
                    risk_signal = self._risk_agent.analyse(market_data)

                    if risk_signal.action == "SKIP":
                        logger.debug(
                            "SniperBot: risk agent rejected snipe for %s#%s.",
                            collection,
                            listing.get("token_id"),
                        )
                        continue

                    order = TradeOrder(
                        bot_name=self.name,
                        collection=collection,
                        token_id=str(listing.get("token_id", "0")),
                        action="BUY",
                        price_eth=float(listing.get("price_eth", 0.0)),
                        marketplace=str(listing.get("marketplace", "opensea")),
                        metadata={"rarity_rank": listing.get("rarity_rank")},
                    )
                    self.execute_order(order)

    def _is_snipe_target(
        self, listing: dict[str, Any], floor_price: float
    ) -> bool:
        """Return True if *listing* qualifies as a snipe target."""
        price = float(listing.get("price_eth", float("inf")))

        if price > self._max_price_eth:
            return False

        # Floor discount condition
        if floor_price > 0 and price <= floor_price * (1 - self._floor_discount_pct):
            return True

        # Rarity condition
        rarity_rank = listing.get("rarity_rank")
        collection_size = listing.get("collection_size", 10_000)
        if rarity_rank is not None and collection_size > 0:
            if rarity_rank / collection_size <= self._rarity_top_pct:
                return True

        return False

    # ------------------------------------------------------------------
    # Data fetchers (stubs — replace with real marketplace API calls)
    # ------------------------------------------------------------------

    def _fetch_new_listings(self, collection: str) -> list[dict[str, Any]]:
        """Fetch the latest new listings for *collection*."""
        return []

    def _fetch_floor_price(self, collection: str) -> float:
        """Return the current floor price for *collection* in ETH."""
        return 0.5

    def _build_market_data(
        self, listing: dict[str, Any], floor_price: float
    ) -> dict[str, Any]:
        return {
            "floor_price": floor_price,
            "volume_24h": 50.0,
            "price_change_24h": 0.02,
            "sentiment_score": 0.5,
            "liquidity_score": 0.6,
            "volatility_30d": 0.4,
            "portfolio_value": 10.0,
            "proposed_trade_value": float(listing.get("price_eth", 0.0)),
        }


if __name__ == "__main__":
    import yaml

    logging.basicConfig(level=logging.INFO)
    with open("config/config.yaml") as f:
        cfg = yaml.safe_load(f)
    bot = SniperBot(cfg)
    bot.start()
