#!/usr/bin/env bash

set -ev

# First wait until our kubernetes cluster is available.
until kubectl get namespaces; do
  echo "Waiting for Kubernetes to start..."
  sleep 1
done
echo "Kubernetes is up and running!"

if helm list | grep -q "jupyterhub"; then
    echo "JupyterHub already installed."
    exit 0;
fi


# Shell script to install JupyterHub via official Helm charts into Kubernetes.
helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update

# This takes about 30 seconds, typically:
helm install jupyterhub jupyterhub/jupyterhub

##
# TODO: this can very likely be accomplished instead using helm chart templating:
##
# Restrict the JupyterHub service for security reasons:
#  We do not want people on the same local network as the compute server to
#  get around our proxy!
# This one is dangerous:
kubectl delete service proxy-public

# This is internal to Kubernetes ONLY:
kubectl expose deployment proxy --name=jupyterhub --port=80 --target-port=8000

# Use configmap to load our custom proxy.json configuration into the cluster:
kubectl create configmap proxy-config  --from-literal='proxy.json=[{ "path": "/", "target": "http://jupyterhub", "ws": true }]'

# Load the registration token into a Kubernetes config map.  When CoCalc
# gets setup it puts the token on the filesystem at
#      /cocalc/conf/auth_token
# We load this file into a secret inside Kubernetes:

kubectl create secret generic secret-token --from-file=/cocalc/conf/auth_token

kubectl apply -f /jupyterhub/proxy.yaml
