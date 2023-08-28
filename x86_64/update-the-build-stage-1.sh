
set -v
docker push  sagemathinc/cocalc-compute:latest
docker push  sagemathinc/cocalc-compute:`cat current_commit`
