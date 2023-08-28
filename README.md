# CoCalc Compute Docker

Docker image for adding remote compute capabilities to a CoCalc project.

URL: https://github.com/sagemathinc/cocalc-compute-docker

Run this image as follows to ensure that it has sufficient permissions to use FUSE to mount a filesystem. This won't work without these permissions:

```sh
docker run --name=cocalc-compute --cap-add=SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined -d sagemathinc/cocalc-compute
```
