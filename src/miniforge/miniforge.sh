#!/usr/bin/env bash
set -xeuo pipefail

# https://github.com/conda-forge/miniforge#downloading-the-installer-as-part-of-a-ci-pipeline
wget -q -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3.sh -b -p "/conda"
. /bin/conda-activate.sh

# upgrade all packages
mamba upgrade --all --yes

# merging in what we want (not removing existing packages)
mamba env update --file environment.yml

# this should end up in '/usr/local/...' for jupyter
jupyter kernelspec remove -y python3
python3 -m ipykernel install --name python3 --display-name "Python 3 (Anaconda/Miniforge)"

# cleanup
mamba clean --all --yes
pip cache purge
rm /Miniforge3.sh
