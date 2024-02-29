#!/usr/bin/env bash

set -ev

rm -rf /tmp/open-webui
cd /tmp
git clone https://github.com/open-webui/open-webui.git
cd /tmp/open-webui

export GPU_COUNT=`nvidia-smi -L | wc -l`

RUN='./run-compose.sh --webui[port=3000] --enable-api[port=11434]'

if [ $GPU_COUNT -gt 0 ]; then
  echo "Found $GPU_COUNT GPU's"
  $RUN --enable-gpu[count=$GPU_COUNT] < /dev/null
else
  echo "No GPU's"
  $RUN < /dev/null
fi;