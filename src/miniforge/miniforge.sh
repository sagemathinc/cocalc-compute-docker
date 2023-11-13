#!/usr/bin/env bash
set -xeuo pipefail

# https://github.com/conda-forge/miniforge#downloading-the-installer-as-part-of-a-ci-pipeline
curl -s -L -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3.sh -b -p "${HOME}/conda"
source "${HOME}/conda/etc/profile.d/conda.sh"
source "${HOME}/conda/etc/profile.d/mamba.sh"
conda activate

mamba update
mamba upgrade --all --yes

# installing dependencies
mamba env update --file environment.yml

# cleanup
mamba clean --all --yes
rm -rf "${HOME}/.cache/pip"
