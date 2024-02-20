#!/usr/bin/env bash

set -ev

rm -rf /tmp/open-webui
cd /tmp
git clone https://github.com/open-webui/open-webui.git
cd /tmp/open-webui

export GPU_COUNT=`nvidia-smi -L | wc -l`

if [ $GPU_COUNT -gt 0 ]; then
  echo "Found $GPU_COUNT GPU's"
  ./run-compose.sh --enable-gpu[count=$GPU_COUNT] --webui[port=3000] < /dev/null
else
  echo "No GPU's"
  ./run-compose.sh --webui[port=3000] < /dev/null
fi;