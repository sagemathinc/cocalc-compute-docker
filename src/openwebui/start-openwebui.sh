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

docker logs -f --tail=999 --timestamps open-webui  &
docker logs -f --tail=999 --timestamps ollama  &

# Stop all the extra containers started by docker compose when this script
# receives SIGINT or SIGTERM. Thanks to
#    https://github.com/Supervisor/supervisor/issues/147#issuecomment-454063690
stop_script() {
    cd /tmp/open-webui
    ./run-compose.sh --drop
    exit 0
}
# Wait for supervisor to stop script
trap stop_script SIGINT SIGTERM

while true
do
    sleep 1
done