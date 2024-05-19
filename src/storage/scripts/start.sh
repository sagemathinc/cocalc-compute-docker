#!/usr/bin/env bash
set -ev

./check-env.sh

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