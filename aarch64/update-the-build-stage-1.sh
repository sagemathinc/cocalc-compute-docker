
set -v
docker stop cocalc-compute-test
docker rm cocalc-compute-test
docker push  sagemathinc/cocalc-compute-aarch64:latest
docker push  sagemathinc/cocalc-compute-aarch64:`cat current_commit`
