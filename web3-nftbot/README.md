# 👾✨ Web3 NFT Bot — NFTflow Architecture

> **Einen strikten Aufbau der Container und der bots und agents im NFTflow**
> A strict structure of the containers, bots and agents in the NFTflow.

---

## Architecture Overview

```
╔══════════════════════════════════════════════════════════════════════════╗
║                  NVIDIA AI Enterprise — NFTflow System                  ║
║                        👾 Web3-NFTbot Stack ✨                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                      CONTAINER LAYER                            │   ║
║   │                                                                  │   ║
║   │  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐   │   ║
║   │  │  nftbot-core    │  │  agent-engine   │  │  flow-runner  │   │   ║
║   │  │  (GPU enabled)  │  │  (GPU enabled)  │  │               │   │   ║
║   │  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘   │   ║
║   │           │                    │                    │            │   ║
║   │  ┌────────▼────────┐  ┌────────▼────────┐  ┌───────▼───────┐   │   ║
║   │  │  redis-cache    │  │  postgres-db    │  │  prometheus   │   │   ║
║   │  └─────────────────┘  └─────────────────┘  └───────────────┘   │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        BOT LAYER                                │   ║
║   │                                                                  │   ║
║   │  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐    │   ║
║   │  │  NFTBot 🤖   │   │ SniperBot 🎯 │   │  ArbitrageBot ⚡ │    │   ║
║   │  │              │   │              │   │                  │    │   ║
║   │  │ • Mint watch │   │ • Floor hunt │   │ • Cross-market   │    │   ║
║   │  │ • Buy/Sell   │   │ • Rare track │   │ • Price diff     │    │   ║
║   │  │ • Portfolio  │   │ • Fast exec  │   │ • Instant trade  │    │   ║
║   │  └──────┬───────┘   └──────┬───────┘   └───────┬──────────┘    │   ║
║   │         └──────────────────┴───────────────────┘               │   ║
║   │                             │                                   │   ║
║   │                    Bot Coordinator 🔄                           │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                       AGENT LAYER (AI)                          │   ║
║   │                                                                  │   ║
║   │  ┌───────────────┐  ┌───────────────┐  ┌────────────────────┐  │   ║
║   │  │ MarketAgent 📊│  │ RiskAgent 🛡️  │  │ PortfolioAgent 💼  │  │   ║
║   │  │               │  │               │  │                    │  │   ║
║   │  │ • Price pred  │  │ • Risk score  │  │ • Asset alloc      │  │   ║
║   │  │ • Trend anal  │  │ • Stop loss   │  │ • Rebalancing      │  │   ║
║   │  │ • Sentiment   │  │ • Exposure    │  │ • P&L tracking     │  │   ║
║   │  └───────┬───────┘  └───────┬───────┘  └─────────┬──────────┘  │   ║
║   │          └──────────────────┴──────────────────────┘            │   ║
║   │                             │                                   │   ║
║   │               NVIDIA GPU Inference Engine 🖥️                    │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
║                                                                          ║
║   ┌─────────────────────────────────────────────────────────────────┐   ║
║   │                        NFTflow 🌊                               │   ║
║   │                                                                  │   ║
║   │   Discover ──► Analyse ──► Decide ──► Execute ──► Report        │   ║
║   │      │             │          │           │          │           │   ║
║   │   [Market]     [Agents]   [Bots]      [Web3 TX]   [Dashboard]   │   ║
║   └─────────────────────────────────────────────────────────────────┘   ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Directory Structure

```
web3-nftbot/
├── README.md                   # This file — architecture overview
├── Dockerfile                  # GPU-enabled container definition
├── docker-compose.yml          # Full stack orchestration
│
├── agents/                     # 🤖 AI Agents (NVIDIA GPU-accelerated)
│   ├── __init__.py
│   ├── base_agent.py           # Abstract base class for all agents
│   ├── market_agent.py         # Market analysis & price prediction
│   ├── risk_agent.py           # Risk scoring & position sizing
│   └── portfolio_agent.py      # Portfolio management & rebalancing
│
├── bots/                       # 🎯 Trading Bots
│   ├── __init__.py
│   ├── base_bot.py             # Abstract base class for all bots
│   ├── nft_bot.py              # Core NFT trading bot
│   ├── sniper_bot.py           # NFT sniper (floor/rare hunting)
│   └── arbitrage_bot.py        # Cross-marketplace arbitrage bot
│
├── config/                     # ⚙️ Configuration
│   └── config.yaml             # All runtime configuration
│
└── flow/                       # 🌊 NFTflow Workflow Definitions
    └── nftflow.yaml            # Step-by-step trading flow
```

---

## Container Architecture

Each service runs in its own GPU-enabled Docker container, orchestrated via `docker-compose.yml`:

| Container        | Description                              | GPU | Port  |
|-----------------|------------------------------------------|-----|-------|
| `nftbot-core`   | Main trading bot engine                  | ✅  | 8000  |
| `agent-engine`  | AI agent inference (NVIDIA GPU)          | ✅  | 8001  |
| `flow-runner`   | NFTflow orchestration service            | —   | 8002  |
| `redis-cache`   | High-speed data & event cache            | —   | 6379  |
| `postgres-db`   | Trade history & portfolio database       | —   | 5432  |
| `prometheus`    | Metrics & monitoring                     | —   | 9090  |

---

## Quick Start

```bash
# Build and start the full NFTflow stack
docker compose up --build

# Start only the AI agent engine with GPU support
docker compose up agent-engine

# Run the NFT sniper bot
docker compose run --rm nftbot-core python -m bots.sniper_bot

# View live metrics
open http://localhost:9090
```

---

## NFTflow — Step-by-Step

```
1. DISCOVER  🔍  MarketAgent scans NFT marketplaces for opportunities
     │
     ▼
2. ANALYSE   📊  RiskAgent scores each opportunity (1–10 risk scale)
     │
     ▼
3. DECIDE    🧠  NVIDIA GPU inference selects optimal action
     │
     ▼
4. EXECUTE   ⚡  Bot submits Web3 transaction to blockchain
     │
     ▼
5. REPORT    📈  PortfolioAgent updates P&L and rebalances holdings
```

---

## Bot Types

### 🤖 NFTBot — Core Trading Bot
Handles general NFT buying, selling, and portfolio management. Monitors
mint events, tracks floor prices, and executes standard trades.

### 🎯 SniperBot — Floor & Rarity Hunter
Ultra-fast bot that targets:
- New listings below floor price
- Rare trait NFTs mispriced by sellers
- Flash sales and time-limited drops

### ⚡ ArbitrageBot — Cross-Marketplace Arbitrage
Detects price differences for the same NFT collection across multiple
marketplaces (OpenSea, Blur, LooksRare, X2Y2) and executes instant trades.

---

## Agent Types

### 📊 MarketAgent — Price & Trend Analysis
GPU-accelerated NVIDIA AI model for:
- Real-time price prediction
- Volume trend analysis
- Social sentiment scoring

### 🛡️ RiskAgent — Risk Management
Controls position sizing and risk exposure:
- Per-trade risk scoring (1–10)
- Dynamic stop-loss calculation
- Portfolio exposure limits

### 💼 PortfolioAgent — Asset Management
Tracks and optimizes the NFT portfolio:
- Real-time P&L tracking
- Automatic rebalancing
- Performance attribution

---

## Configuration

All settings are managed through `config/config.yaml`. Key sections:

- **`bots`** — Enable/disable bots, set budget limits and strategies
- **`agents`** — AI model paths, inference settings, GPU allocation
- **`web3`** — RPC endpoints, wallet configuration, gas strategy
- **`flow`** — NFTflow step timeouts and retry policies
- **`monitoring`** — Metrics, alerts and notification channels

---

## Security Notes

- Private keys are **never** stored in config files — use environment variables or a secrets manager.
- All containers run as non-root users.
- Network access is restricted to necessary endpoints only.
