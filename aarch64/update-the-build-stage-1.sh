
set -v
docker push  sagemathinc/cocalc-compute-aarch64:latest
docker push  sagemathinc/cocalc-compute-aarch64:`cat current_commit`
