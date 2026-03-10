"""Tests for the NFTflow agent layer."""

import pytest
import sys
import os

# Add the web3-nftbot directory to the path so imports work without installing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), ".."),
)

from agents.base_agent import AgentSignal
from agents.market_agent import MarketAgent
from agents.risk_agent import RiskAgent
from agents.portfolio_agent import PortfolioAgent

# ─── Fixtures ────────────────────────────────────────────────────────────────

MINIMAL_CONFIG: dict = {
    "agents": {
        "market_model_path": "models/market_predictor.onnx",
        "gpu_device": -1,
        "portfolio_drift_threshold": 0.10,
        "stop_loss_pct": 0.20,
        "take_profit_pct": 0.50,
    },
    "bots": {
        "max_trade_pct_portfolio": 0.05,
    },
}


@pytest.fixture
def market_agent() -> MarketAgent:
    agent = MarketAgent(MINIMAL_CONFIG)
    agent.start()
    return agent


@pytest.fixture
def risk_agent() -> RiskAgent:
    agent = RiskAgent(MINIMAL_CONFIG)
    agent.start()
    return agent


@pytest.fixture
def portfolio_agent() -> PortfolioAgent:
    agent = PortfolioAgent(MINIMAL_CONFIG)
    agent.start()
    return agent


# ─── AgentSignal ─────────────────────────────────────────────────────────────


class TestAgentSignal:
    def test_valid_signal(self):
        sig = AgentSignal(agent_name="test", action="BUY", confidence=0.8)
        assert sig.agent_name == "test"
        assert sig.action == "BUY"
        assert sig.confidence == 0.8

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValueError):
            AgentSignal(agent_name="test", action="BUY", confidence=1.5)

    def test_confidence_zero_is_valid(self):
        sig = AgentSignal(agent_name="test", action="HOLD", confidence=0.0)
        assert sig.confidence == 0.0

    def test_confidence_one_is_valid(self):
        sig = AgentSignal(agent_name="test", action="SELL", confidence=1.0)
        assert sig.confidence == 1.0


# ─── MarketAgent ─────────────────────────────────────────────────────────────


class TestMarketAgent:
    def test_is_ready_after_start(self, market_agent):
        assert market_agent.is_ready

    def test_analyse_returns_signal(self, market_agent):
        data = {
            "floor_price": 1.0,
            "volume_24h": 100.0,
            "price_change_24h": 0.2,
            "sentiment_score": 0.8,
        }
        signal = market_agent.analyse(data)
        assert isinstance(signal, AgentSignal)
        assert signal.agent_name == "MarketAgent"
        assert signal.action in {"BUY", "SELL", "HOLD"}
        assert 0.0 <= signal.confidence <= 1.0

    def test_bullish_data_gives_buy(self, market_agent):
        data = {
            "price_change_24h": 1.0,
            "sentiment_score": 1.0,
        }
        signal = market_agent.analyse(data)
        assert signal.action == "BUY"

    def test_bearish_data_gives_sell(self, market_agent):
        data = {
            "price_change_24h": -1.0,
            "sentiment_score": -1.0,
        }
        signal = market_agent.analyse(data)
        assert signal.action == "SELL"

    def test_neutral_data_gives_hold(self, market_agent):
        data = {
            "price_change_24h": 0.0,
            "sentiment_score": 0.0,
        }
        signal = market_agent.analyse(data)
        assert signal.action == "HOLD"

    def test_not_started_raises(self):
        agent = MarketAgent(MINIMAL_CONFIG)
        with pytest.raises(RuntimeError):
            agent.analyse({})

    def test_repr(self, market_agent):
        assert "MarketAgent" in repr(market_agent)
        assert "ready=True" in repr(market_agent)


# ─── RiskAgent ───────────────────────────────────────────────────────────────


class TestRiskAgent:
    def test_is_ready_after_start(self, risk_agent):
        assert risk_agent.is_ready

    def test_analyse_returns_signal(self, risk_agent):
        data = {
            "volatility_30d": 0.2,
            "liquidity_score": 0.8,
            "portfolio_value": 10.0,
            "proposed_trade_value": 0.5,
        }
        signal = risk_agent.analyse(data)
        assert isinstance(signal, AgentSignal)
        assert signal.action in {"PROCEED", "REDUCE", "SKIP"}
        assert 0.0 <= signal.confidence <= 1.0

    def test_low_volatility_high_liquidity_proceeds(self, risk_agent):
        data = {
            "volatility_30d": 0.0,
            "liquidity_score": 1.0,
            "portfolio_value": 10.0,
        }
        signal = risk_agent.analyse(data)
        assert signal.action == "PROCEED"

    def test_high_volatility_low_liquidity_skips(self, risk_agent):
        data = {
            "volatility_30d": 1.0,
            "liquidity_score": 0.0,
            "portfolio_value": 10.0,
        }
        signal = risk_agent.analyse(data)
        assert signal.action == "SKIP"

    def test_risk_score_in_metadata(self, risk_agent):
        data = {
            "volatility_30d": 0.3,
            "liquidity_score": 0.5,
            "portfolio_value": 10.0,
        }
        signal = risk_agent.analyse(data)
        assert "risk_score" in signal.metadata
        assert 1 <= signal.metadata["risk_score"] <= 10

    def test_max_trade_size_in_metadata(self, risk_agent):
        data = {
            "volatility_30d": 0.0,
            "liquidity_score": 1.0,
            "portfolio_value": 100.0,
        }
        signal = risk_agent.analyse(data)
        assert "max_trade_size_eth" in signal.metadata
        assert signal.metadata["max_trade_size_eth"] >= 0


# ─── PortfolioAgent ──────────────────────────────────────────────────────────


class TestPortfolioAgent:
    def test_is_ready_after_start(self, portfolio_agent):
        assert portfolio_agent.is_ready

    def test_empty_holdings_gives_hold(self, portfolio_agent):
        data: dict = {
            "holdings": [],
            "target_weights": {},
            "stop_loss_pct": 0.20,
            "take_profit_pct": 0.50,
        }
        signal = portfolio_agent.analyse(data)
        assert signal.action == "HOLD"

    def test_stop_loss_triggers_exit(self, portfolio_agent):
        data = {
            "holdings": [
                {
                    "collection": "bayc",
                    "quantity": 1,
                    "current_value": 0.7,
                    "cost_basis": 1.0,
                }
            ],
            "target_weights": {"bayc": 1.0},
            "stop_loss_pct": 0.20,
            "take_profit_pct": 0.50,
        }
        signal = portfolio_agent.analyse(data)
        assert signal.action == "EXIT"
        assert "bayc" in signal.metadata["exit_positions"]

    def test_take_profit_triggers_exit(self, portfolio_agent):
        data = {
            "holdings": [
                {
                    "collection": "mayc",
                    "quantity": 1,
                    "current_value": 2.0,
                    "cost_basis": 1.0,
                }
            ],
            "target_weights": {"mayc": 1.0},
            "stop_loss_pct": 0.20,
            "take_profit_pct": 0.50,
        }
        signal = portfolio_agent.analyse(data)
        assert signal.action == "EXIT"

    def test_drift_triggers_rebalance(self, portfolio_agent):
        data = {
            "holdings": [
                {"collection": "a", "quantity": 1, "current_value": 9.0, "cost_basis": 5.0},
                {"collection": "b", "quantity": 1, "current_value": 1.0, "cost_basis": 5.0},
            ],
            "target_weights": {"a": 0.50, "b": 0.50},
            "stop_loss_pct": 0.99,   # disable stop-loss for this test
            "take_profit_pct": 10.0,  # disable take-profit for this test
        }
        signal = portfolio_agent.analyse(data)
        assert signal.action == "REBALANCE"

    def test_pnl_in_metadata(self, portfolio_agent):
        data = {
            "holdings": [
                {"collection": "c", "quantity": 1, "current_value": 1.5, "cost_basis": 1.0},
            ],
            "target_weights": {},
            "stop_loss_pct": 0.99,
            "take_profit_pct": 10.0,
        }
        signal = portfolio_agent.analyse(data)
        assert "pnl_summary" in signal.metadata
        pnl = signal.metadata["pnl_summary"]
        assert pnl["pnl"] == pytest.approx(0.5)
        assert pnl["pnl_pct"] == pytest.approx(0.5)
