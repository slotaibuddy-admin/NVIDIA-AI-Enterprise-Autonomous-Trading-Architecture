"""Tests for the NFTflow bot layer."""

import sys
import os
from typing import Any
from unittest.mock import patch

import pytest

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), ".."),
)

from bots.base_bot import BotStatus, TradeOrder
from bots.sniper_bot import SniperBot
from bots.arbitrage_bot import ArbitrageBot

# ─── Fixtures ────────────────────────────────────────────────────────────────

MINIMAL_CONFIG: dict[str, Any] = {
    "agents": {
        "market_model_path": "models/stub.onnx",
        "gpu_device": -1,
        "portfolio_drift_threshold": 0.10,
        "stop_loss_pct": 0.20,
        "take_profit_pct": 0.50,
    },
    "bots": {
        "max_trade_pct_portfolio": 0.05,
        "poll_interval_seconds": 30,
        "watched_collections": ["0xtest"],
        "sniper": {
            "floor_discount_pct": 0.05,
            "rarity_top_pct": 0.10,
            "max_price_eth": 1.0,
            "poll_interval_seconds": 5,
        },
        "arbitrage": {
            "min_profit_eth": 0.01,
            "gas_estimate_eth": 0.005,
            "marketplaces": ["opensea", "blur"],
            "poll_interval_seconds": 10,
        },
    },
    "web3": {
        "default_marketplace": "opensea",
    },
}


# ─── TradeOrder ──────────────────────────────────────────────────────────────


class TestTradeOrder:
    def test_buy_order(self):
        order = TradeOrder(
            bot_name="TestBot",
            collection="0xabc",
            token_id="42",
            action="BUY",
            price_eth=0.5,
            marketplace="opensea",
        )
        assert order.action == "BUY"
        assert order.price_eth == 0.5

    def test_sell_order(self):
        order = TradeOrder(
            bot_name="TestBot",
            collection="0xabc",
            token_id="42",
            action="SELL",
            price_eth=1.2,
            marketplace="blur",
        )
        assert order.action == "SELL"
        assert order.marketplace == "blur"


# ─── SniperBot ───────────────────────────────────────────────────────────────


class TestSniperBot:
    def _make_bot(self) -> SniperBot:
        return SniperBot(MINIMAL_CONFIG)

    def test_initial_status_is_idle(self):
        bot = self._make_bot()
        assert bot.status == BotStatus.IDLE

    def test_is_snipe_target_floor_discount(self):
        bot = self._make_bot()
        listing = {"price_eth": 0.9, "token_id": "1", "collection_size": 10000}
        # Floor = 1.0, discount = 5% → target price <= 0.95
        assert bot._is_snipe_target(listing, floor_price=1.0)

    def test_not_snipe_target_above_floor(self):
        bot = self._make_bot()
        listing = {"price_eth": 1.1, "token_id": "1", "collection_size": 10000}
        assert not bot._is_snipe_target(listing, floor_price=1.0)

    def test_is_snipe_target_rarity(self):
        bot = self._make_bot()
        # Rarity rank 50 out of 10000 = top 0.5% → within top 10% threshold
        listing = {
            "price_eth": 0.99,  # just below max_price_eth=1.0
            "token_id": "50",
            "rarity_rank": 50,
            "collection_size": 10000,
        }
        # Not a floor snipe (price 0.99 vs floor 1.0 → only 1% below, need 5%)
        # But IS a rarity snipe
        assert bot._is_snipe_target(listing, floor_price=1.0)

    def test_exceeds_max_price_not_target(self):
        bot = self._make_bot()
        listing = {
            "price_eth": 2.0,  # above max_price_eth=1.0
            "rarity_rank": 1,
            "collection_size": 10000,
            "token_id": "1",
        }
        assert not bot._is_snipe_target(listing, floor_price=1.0)

    def test_execute_order_returns_true(self):
        bot = self._make_bot()
        order = TradeOrder(
            bot_name=bot.name,
            collection="0xtest",
            token_id="99",
            action="BUY",
            price_eth=0.5,
            marketplace="opensea",
        )
        assert bot.execute_order(order) is True

    def test_repr(self):
        bot = self._make_bot()
        assert "SniperBot" in repr(bot)
        assert "idle" in repr(bot)


# ─── ArbitrageBot ────────────────────────────────────────────────────────────


class TestArbitrageBot:
    def _make_bot(self) -> ArbitrageBot:
        return ArbitrageBot(MINIMAL_CONFIG)

    def test_initial_status_is_idle(self):
        bot = self._make_bot()
        assert bot.status == BotStatus.IDLE

    def test_find_best_opportunity_returns_none_when_no_prices(self):
        bot = self._make_bot()
        result = bot._find_best_opportunity({})
        assert result is None

    def test_find_best_opportunity_returns_none_single_market(self):
        bot = self._make_bot()
        prices = {"token1": {"opensea": 1.0}}
        result = bot._find_best_opportunity(prices)
        assert result is None

    def test_find_best_opportunity_returns_spread(self):
        bot = self._make_bot()
        prices = {
            "token1": {
                "opensea": 1.0,
                "blur": 1.5,
            }
        }
        result = bot._find_best_opportunity(prices)
        assert result is not None
        buy_market, token_id, buy_price, sell_market, sell_price = result
        assert buy_market == "opensea"
        assert sell_market == "blur"
        assert buy_price == 1.0
        assert sell_price == 1.5
        assert token_id == "token1"

    def test_execute_order_returns_true(self):
        bot = self._make_bot()
        order = TradeOrder(
            bot_name=bot.name,
            collection="0xtest",
            token_id="1",
            action="BUY",
            price_eth=1.0,
            marketplace="opensea",
        )
        assert bot.execute_order(order) is True

    def test_min_profit_filters_small_spreads(self):
        bot = self._make_bot()
        # Spread = 0.005, gas = 0.005 → net profit = 0, below min_profit_eth=0.01
        prices = {
            "token1": {
                "opensea": 1.000,
                "blur": 1.005,
            }
        }
        with patch.object(
            bot, "_fetch_prices_across_markets", return_value=prices
        ):
            bot._risk_agent.start()
            # Should not call execute_order since profit < min threshold
            with patch.object(bot, "execute_order") as mock_exec:
                bot._scan_for_arbitrage()
                mock_exec.assert_not_called()

    def test_successful_execution_when_profit_exceeds_threshold(self):
        bot = self._make_bot()
        # Spread = 0.1, gas = 0.005 → net profit = 0.095, above min_profit_eth=0.01
        prices = {
            "token1": {
                "opensea": 1.0,
                "blur": 1.1,
            }
        }
        with patch.object(
            bot, "_fetch_prices_across_markets", return_value=prices
        ):
            bot._risk_agent.start()
            with patch.object(bot, "execute_order", return_value=True) as mock_exec:
                bot._scan_for_arbitrage()
                # Expect two orders: one BUY and one SELL
                assert mock_exec.call_count == 2
                buy_order = mock_exec.call_args_list[0][0][0]
                sell_order = mock_exec.call_args_list[1][0][0]
                assert buy_order.action == "BUY"
                assert buy_order.marketplace == "opensea"
                assert sell_order.action == "SELL"
                assert sell_order.marketplace == "blur"

    def test_risk_rejection_suppresses_execution(self):
        bot = self._make_bot()
        # Large spread that would otherwise qualify
        prices = {
            "token1": {
                "opensea": 1.0,
                "blur": 2.0,
            }
        }
        with patch.object(
            bot, "_fetch_prices_across_markets", return_value=prices
        ):
            bot._risk_agent.start()
            # Force risk agent to always SKIP
            from agents.base_agent import AgentSignal
            skip_signal = AgentSignal(
                agent_name="RiskAgent", action="SKIP", confidence=1.0
            )
            with patch.object(bot._risk_agent, "analyse", return_value=skip_signal):
                with patch.object(bot, "execute_order") as mock_exec:
                    bot._scan_for_arbitrage()
                    mock_exec.assert_not_called()

    def test_repr(self):
        bot = self._make_bot()
        assert "ArbitrageBot" in repr(bot)
