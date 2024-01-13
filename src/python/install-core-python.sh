#!/usr/bin/env bash

set -ev

# Install pip and Jupyter
apt-get update
apt-get install -y python3-pip
pip install jupyter
python3 -m ipykernel install

# Install the very popular python libraries, which are pretty
# safe to install in any python environment.
pip install matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx
