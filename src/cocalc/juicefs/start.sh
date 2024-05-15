#!/usr/bin/env bash
set -ev

export SERVICE_ACCOUNT=/secrets/google-service-account.json
export BUCKET=compute-server-storage-2
export COMPUTE_SERVER_ID=3767
export MOUNT=/home/user/jfs

# Configure google cloud storage credentials

export GOOGLE_APPLICATION_CREDENTIALS=$SERVICE_ACCOUNT

# Mount the google cloud storage bucket at /bucket
sudo mkdir -p /bucket
sudo chown user:user /bucket
gcsfuse $BUCKET /bucket

# Start keydb
./start-keydb.sh

# Start juicefs
./start-juicefs.sh