#!/usr/bin/env bash

# Shell script to install JupyterHub via official Helm charts into Kubernetes.

helm repo add jupyterhub https://hub.jupyter.org/helm-chart/
helm repo update
helm install jupyterhub jupyterhub/jupyterhub

# Make jupyterhub ONLY listen on localhost port 80
kubectl apply -f /jupyterhub/ingress.yaml