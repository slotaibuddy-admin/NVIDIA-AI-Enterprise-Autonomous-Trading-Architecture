# NFTflow Container and Agent Layout

This guide documents a strict, containerised layout for a Web3 NFT bot pipeline (NFTflow). It highlights which services live in their own containers, which responsibilities belong to bots versus system agents, and how information moves through the flow.

## Design Principles
- **Strict isolation**: Each concern (ingress, orchestration, strategy, wallets, observability) is deployed as an independent container with only the permissions it needs.
- **Event-driven backbone**: All bots consume and emit events over a message bus to keep coupling low and scaling simple.
- **Reproducible builds**: Images are pinned and built from the same base to ensure deterministic runtime behaviour.
- **GPU-ready where needed**: Model/feature containers are the only ones that require GPUs; keep everything else CPU-only to reduce blast radius.

## Container Topology (pictured)
```
                       +------------------+
                       |  User/API Client |
                       +------------------+
                                |
                                v
+-------------------+    +---------------+    +------------------+
| Ingress Gateway   |--> | Message Bus   |--> | Scheduler/Orchestrator |
| (REST/Webhook)    |    | (Kafka/NATS)  |    | (Argo/Airflow)    |
+-------------------+    +---------------+    +------------------+
                                                   |
                                                   v
       +--------------------+   +----------------------+   +-----------------------+
       | Data Collector     |   | Feature/Model Svc    |   | Strategy Bots         |
       | (RPC/subgraphs)    |   | (GPU optional)       |   | (mint/buy/list logic) |
       +--------------------+   +----------------------+   +-----------------------+
                     \\             |                               |
                      \\            v                               v
                       \\   +---------------------+        +------------------+
                        --> | Wallet/Key Manager  | <------| Risk/Compliance  |
                            +---------------------+        +------------------+
                                       |
                                       v
                            +---------------------+
                            | Blockchain Gateway  |
                            | (RPC/relayer)       |
                            +---------------------+
                                       |
                                       v
                          +-----------------------+
                          | Observability/Storage |
                          | (Prom/Grafana/DB)     |
                          +-----------------------+
```

## Container Responsibilities
- **Ingress Gateway**: Terminates TLS, validates webhook signatures, throttles input, and publishes events to the bus.
- **Message Bus**: Durable queue for market data, triggers, and bot actions. Example: Kafka, NATS, or Redis Streams.
- **Scheduler/Orchestrator**: Runs DAGs and timed jobs that fan out work to strategy bots; handles retries and backoff.
- **Data Collector**: Normalises on-chain events (mempool, subgraphs, NFT marketplaces) into canonical messages.
- **Feature/Model Service (GPU)**: Computes scores/forecasts; exposes gRPC/REST. The only container that requests `nvidia.com/gpu`.
- **Strategy Bots**: Stateless workers consuming events and producing intents (mint, bid, list, sweep). Packaged as horizontally scalable containers.
- **Risk/Compliance Agent**: Blocks intents violating policy (blocked collections, spend limits, slippage bounds).
- **Wallet/Key Manager**: Signs intents using HSM/KMS; never shares keys with bots. Provides short-lived signing endpoints.
- **Blockchain Gateway**: Relays signed transactions to RPC providers or custom full nodes; handles nonce and gas management.
- **Observability/Storage**: Central logging, metrics, traces, and state (Postgres/ClickHouse). Bots never write directly to blockchain RPC logs.

## Bot and Agent Roles
- **Bots** focus on decision-making: identifying opportunities and proposing actions.
- **Agents** enforce guardrails: risk checks, signing, compliance, and deployment orchestration.
- **Communication** always flows through the message bus; bots never call the wallet directly.

## Reference Flow
1. Marketplace/webhook hits **Ingress Gateway**.
2. Gateway validates and publishes to **Message Bus**.
3. **Scheduler** fans out to **Data Collector** and **Strategy Bots**.
4. Bots request scores from **Feature/Model Service** when required.
5. Bots emit intents; **Risk Agent** approves/rejects.
6. Approved intents are signed by **Wallet/Key Manager**.
7. **Blockchain Gateway** submits transactions and tracks receipts.
8. Metrics, logs, and state land in **Observability/Storage**.

## Deployment Notes
- Use separate namespaces for `ingress`, `compute`, `signing`, and `observability`.
- Pin image tags; enforce read-only root FS for bots and agents.
- Route GPU requests only to the `feature/model` deployment to keep other pods schedulable on CPU nodes.
- Expose wallet and blockchain gateways on private networks only; ingress never reaches them directly.
