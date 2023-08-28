
set -v
docker stop cocalc-compute-test
docker rm cocalc-compute-test
docker push  sagemathinc/cocalc-compute:latest
docker push  sagemathinc/cocalc-compute:`cat current_commit`
