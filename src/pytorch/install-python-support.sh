#!/usr/bin/env bash

set -ev

# To easily install certain things from Hugging Face, we install
# libraries that huggingface libraries use.
apt-get update
apt-get install -y ffmpeg libsm6 libxext6

pip install diffusers transformers diffusers invisible_watermark accelerate safetensors sentencepiece

# Also, some popular python libraries
pip install matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx
