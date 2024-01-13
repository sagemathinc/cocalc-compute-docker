#!/usr/bin/env bash

set -ev

# To easily install certain things from Hugging Face, we install
# libraries that huggingface libraries use.
apt-get update
apt-get install -y ffmpeg libsm6 libxext6

pip install diffusers transformers diffusers invisible_watermark accelerate safetensors sentencepiece
