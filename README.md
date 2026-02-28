# NVIDIA Container Toolkit

[![GitHub license](https://img.shields.io/github/license/NVIDIA/nvidia-container-toolkit?style=flat-square)](https://raw.githubusercontent.com/NVIDIA/nvidia-container-toolkit/main/LICENSE)
[![Documentation](https://img.shields.io/badge/documentation-wiki-blue.svg?style=flat-square)](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html)
[![Package repository](https://img.shields.io/badge/packages-repository-b956e8.svg?style=flat-square)](https://nvidia.github.io/libnvidia-container)

![nvidia-container-stack](https://cloud.githubusercontent.com/assets/3028125/12213714/5b208976-b632-11e5-8406-38d379ec46aa.png)

## Introduction

The NVIDIA Container Toolkit allows users to build and run GPU-accelerated containers. The toolkit includes a container runtime [library](https://github.com/NVIDIA/libnvidia-container) and utilities to automatically configure containers to leverage NVIDIA GPUs.

Product documentation including an architecture overview, platform support, and installation and usage guides can be found in the [documentation repository](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/overview.html).

## Getting Started

**Make sure you have installed the [NVIDIA driver](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#nvidia-drivers) for your Linux Distribution**
**Note that you do not need to install the CUDA Toolkit on the host system, but the NVIDIA driver needs to be installed**

For instructions on getting started with the NVIDIA Container Toolkit, refer to the [installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#installation-guide).

## Usage

The [user guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/user-guide.html) provides information on the configuration and command line options available when running GPU containers with Docker.

### Running Large Language Models (LLMs)

The NVIDIA Container Toolkit enables running large language models like Meta's Llama 3.1-70B using NVIDIA NIM (NVIDIA Inference Microservices). Below is an example using Docker:

**Prerequisites:**
- Multiple A100 (80GB) or H100 GPUs with at least 140GB total GPU memory
- NVIDIA driver version 535 or later
- NGC API key from [NVIDIA NGC](https://ngc.nvidia.com)

**Example: Running Llama 3.1-70B**

```sh
# Set your NGC API key
export NGC_API_KEY=<your-ngc-api-key>
export LOCAL_NIM_CACHE=~/.cache/nim
mkdir -p "$LOCAL_NIM_CACHE"

# Run Llama 3.1-70B using NVIDIA NIM
docker run -it --rm \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -u $(id -u) \
    -p 8000:8000 \
    nvcr.io/nim/meta/llama-3.1-70b-instruct:latest
```

For more information on running LLMs with NVIDIA NIM, refer to the [NVIDIA NIM documentation](https://docs.nvidia.com/nim/large-language-models/latest/getting-started.html).

## Issues and Contributing

[Checkout the Contributing document!](CONTRIBUTING.md)

* Please let us know by [filing a new issue](https://github.com/NVIDIA/nvidia-container-toolkit/issues/new)
* You can contribute by creating a [pull request](https://github.com/NVIDIA/nvidia-container-toolkit/compare) to our public GitHub repository
