#!/usr/bin/env bash

if [ -z $SERVICE_ACCOUNT ]; then
    echo "Environment variable SERVICE_ACCOUNT must be set to the path of the Google cloud service account json file"
    exit 1
fi

if [ -z $BUCKET ]; then
    echo "Environment variable BUCKET must be set to the name of the Google cloud bucket"
    exit 1
fi

if [ -z $COMPUTE_SERVER_ID ]; then
    echo "Environment variable COMPUTE_SERVER_ID must be set to the numerical id of the compute server"
    exit 1
fi

if [ -z $MOUNT ]; then
    echo "Environment variable MOUNT must be set to the mount point"
    exit 1
fi
