#!/usr/bin/env bash
set -xeuo pipefail

# Colab runs Python 3.10
python -V

pip install -U pip

# we get rid of google colab itself
sed -i '/google-colab @ file/d' env.txt

pip --no-cache-dir install -r env.txt
pip cache purge

