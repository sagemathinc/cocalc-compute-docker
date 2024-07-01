#!/usr/bin/env bash

set -ev

if [ $# -lt 1 ]; then
  echo "Error: At least one argument is required."
  exit 1
fi

export IMAGE="$1"
export ARCH_TAG="${2:-latest}"
export TAG="${3:-$ARCH_TAG}"

echo IMAGE=$IMAGE
echo ARCH_TAG=$ARCH_TAG
echo TAG=$TAG

attempt=0
until docker manifest create   $IMAGE:$TAG $IMAGE-x86_64:$ARCH_TAG $IMAGE-arm64:$ARCH_TAG --amend; do
  attempt=$((attempt+1))
  if [[ $attempt -ge 50 ]]; then
    echo "Command failed after 30 attempts, exiting..."
    exit 1
  fi
  echo "Command failed, retrying in 10 seconds..."
  sleep 10
done


docker manifest annotate $IMAGE:$TAG $IMAGE-x86_64:$ARCH_TAG --os linux --arch amd64
docker manifest annotate $IMAGE:$TAG $IMAGE-arm64:$ARCH_TAG  --os linux --arch arm64
docker manifest push     $IMAGE:$TAG
