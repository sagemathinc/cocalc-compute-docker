#!/usr/bin/env bash
set -xeuo pipefail

# Colab runs Python 3.10
#python -V

# 2023-11-17: only jammy and jammy-updates (for Ubuntu 22.04)
cat apt.txt | tail -n +2 | grep "/$(lsb_release -s -c)" | cut -d'/' -f1 | xargs apt-get install -y

pip install -U pip
# we get rid of google colab itself
sed -i '/google-colab @ file/d' env.txt

pip --no-cache-dir install -r env.txt

# env.txt should contain an ipykernel, we just ensure it is here, no updating!
pip install ipykernel
jupyter kernelspec remove -y python3
python3 -m ipykernel install --sys-prefix --name python3 --display-name "Python 3 (Colab)"

pip cache purge
