# syntax=docker/dockerfile:1
# NVIDIA GPU-enabled container for Web3-NFTbot (NFTflow)

ARG CUDA_VERSION=12.3.0
ARG UBUNTU_VERSION=22.04

FROM nvcr.io/nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu${UBUNTU_VERSION}

LABEL maintainer="NVIDIA AI Enterprise"
LABEL description="Web3 NFT Bot — NFTflow container (GPU-accelerated)"
LABEL version="1.0.0"

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-dev \
        python3-pip \
        libssl-dev \
        libffi-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# --- Create non-root user ---
RUN groupadd --gid 1001 nftbot \
    && useradd --uid 1001 --gid nftbot --shell /bin/bash --create-home nftbot

WORKDIR /app

# --- Python dependencies ---
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

# --- Copy application source ---
COPY --chown=nftbot:nftbot agents/ ./agents/
COPY --chown=nftbot:nftbot bots/   ./bots/
COPY --chown=nftbot:nftbot config/ ./config/
COPY --chown=nftbot:nftbot flow/   ./flow/

# --- Switch to non-root user ---
USER nftbot

# --- NVIDIA runtime requirements ---
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

# --- Default entrypoint: run the core NFT bot ---
ENTRYPOINT ["python3", "-m", "bots.nft_bot"]
