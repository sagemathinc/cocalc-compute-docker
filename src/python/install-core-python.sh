#!/usr/bin/env bash

set -ev

# Install pip and Jupyter
apt-get update
apt-get install -y python3-pip python3-dev

pip install --break-system-packages jupyter
python3 -m ipykernel install --name python3 --display-name "Python `python3 --version | awk '{print $2}'`"

# Install the very popular python libraries, which are pretty
# safe to install in any python environment.
pip install --break-system-packages  matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx

