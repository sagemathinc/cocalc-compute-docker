# Script for extracting tag from images.json file.
GET_TAG=./src/scripts/get-tag.js images.json
GET_VERSION=./src/scripts/get-version.js images.json

# Docker image parameters
DOCKER_USER=sagemathinc
TAG=

# CoCalc Git parameters
BRANCH=master

COMMIT=$(shell git ls-remote -h https://github.com/sagemathinc/cocalc $(BRANCH) | awk '{print $$1}')

# ARCH = '-x86_64' or '-arm64'
ARCH=$(shell uname -m | sed 's/x86_64/-x86_64/;s/arm64/-arm64/;s/aarch64/-arm64/')

# ARCH0 = '' or '-arm64'
ARCH0=$(shell uname -m | sed 's/x86_64//;s/arm64/-arm64/;s/aarch64/-arm64/')

# ARCH1 = 'amd64' or 'arm64'
ARCH1=$(shell uname -m | sed 's/x86_64/amd64/;s/arm64/arm64/;s/aarch64/arm64/')


all-x86:
	make core && make math && make gpu
push-all-x86:
	make push-core && make push-math && make push-gpu
all-arm64:
	make core && make math
push-all-arm64:
	make push-core && make push-math

prune-all:
	time docker system prune -a

core:
	make base && make cocalc && make filesystem && make compute && make python && make anaconda && make openwebui
push-core:
	make push-base && make push-filesystem && make push-compute && make push-python  && make push-anaconda && make push-openwebui
assemble-core:
	make assemble-base && make assemble-filesystem && make assemble-compute && make assemble-python  && make assemble-anaconda && make assemble-openwebui && make assemble-lean

## IMAGE: cocalc

# This "cocalc" is the subset of the cocalc nodejs code
# needed to run cocalc directly on the compute server
# for supporting websocketfs mounting, terminals, and jupyter notebooks.
# We build a docker image on the build host, but then copy the files out
# there, compress them, and push them to npmjs.com!  This is never pushed
# to dockerhub, and docker is just used for convenience to make the build
# easier.  We push two packages to npm, one for each arch.

COCALC_TAG=test
cocalc:
	cd src/cocalc && docker build --build-arg COMMIT=$(COMMIT) --build-arg BRANCH=$(BRANCH)  --build-arg ARCH=${ARCH} --build-arg BASE_TAG=$(BASE_TAG)  -t $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG) .

run-cocalc:
	docker run --network=host --name run-cocalc -it --rm $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG)

# Try to build something that matches /cocalc on a production compute server.
# This is done via src/packages/server/compute/cloud/install.ts and startup-script.ts
# when the compute server starts. We do the same here (more or less) for testing purposes.
# https://github.com/sagemathinc/cocalc/issues/6963
NODE_VERSION=18.17.1
# see https://github.com/nvm-sh/nvm#install--update-script for this version:
NVM_VERSION=0.39.5
rm-tmp-cocalc:
	rm /tmp/cocalc/done
/tmp/cocalc/done:
	rm -rf /tmp/cocalc
	docker rm temp-copy-cocalc || true
	docker create --name temp-copy-cocalc $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG)
	docker cp temp-copy-cocalc:/cocalc /tmp/cocalc
	docker rm temp-copy-cocalc
	cp -rv $(COCALC_NPM)/* /tmp/cocalc
	mkdir -p /tmp/cocalc/nvm
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v$(NVM_VERSION)/install.sh | NVM_DIR=/tmp/cocalc/nvm PROFILE=/dev/null bash
	bash -c "unset NVM_DIR NVM_BIN NVM_INC && source /tmp/cocalc/nvm/nvm.sh && nvm install --no-progress $(NODE_VERSION)"
	rm -rf /tmp/cocalc/nvm/.cache
	mkdir -p /tmp/cocalc/conf
	cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 8 | head -n 1 > /tmp/cocalc/conf/auth_token
	node -e "const data = require('fs').readFileSync('images.json'); const json = JSON.parse(data); console.log(JSON.stringify(json.defaults.proxy,0,2));" > /tmp/cocalc/conf/proxy.json
	touch /tmp/cocalc/done

# Copy from docker image and publish @cocalc/compute-cocalc$(ARCH)
# to the npm registry.  This only works, of course, if you are signed
# into npm as a user that can publish to @cocalc.
COCALC_NPM=src/cocalc-npm
COCALC_VERSION=$(shell $(GET_VERSION) cocalc $(COCALC_TAG))
push-cocalc:
	rm -rf /tmp/cocalc-npm$(ARCH0)
	mkdir -p /tmp/cocalc-npm$(ARCH0)/dist
	cp -rv $(COCALC_NPM)/* /tmp/cocalc-npm$(ARCH0)
	docker rm temp-copy-cocalc || true
	docker create --name temp-copy-cocalc $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG)
	docker cp temp-copy-cocalc:/cocalc /tmp/cocalc-npm$(ARCH0)/dist/cocalc
	docker rm temp-copy-cocalc
	cd /tmp/cocalc-npm$(ARCH0)/dist/ && tar -zcf cocalc.tar.gz cocalc
	rm -r /tmp/cocalc-npm$(ARCH0)/dist/cocalc/
	# Add -arm64 extension to package name, if necessary.
	@if [ -n "$(ARCH0)" ]; then sed -i.bak 's/compute-server/compute-server-arm64/g' /tmp/cocalc-npm$(ARCH0)/package.json; fi
	cd /tmp/cocalc-npm$(ARCH0) \
		&& npm version $(COCALC_VERSION) \
		&& npm publish --access=public --no-git-checks --tag=$(COCALC_TAG)
	# Comment this line out if you want to do something by hand, like explicitly set the version number on npmjs.
	rm -rf /tmp/cocalc-npm$(ARCH0)

## IMAGE: base
# We build base-x86_64 and base-arm64.
# They are pushed to dockerhub.
# We also run the assemble target to create the multiplatform
#     $(DOCKER_USER)/base
# which is what gets used everywhere else.
BASE_TAG = $(shell $(GET_TAG) base)
base:
	cd src/base && docker build -t $(DOCKER_USER)/base$(ARCH):$(BASE_TAG) .
run-base:
	docker run --name run-base -it --rm $(DOCKER_USER)/base$(ARCH):$(BASE_TAG) bash
push-base:
	docker push $(DOCKER_USER)/base$(ARCH):$(BASE_TAG)
assemble-base:
	./src/scripts/assemble.sh $(DOCKER_USER)/base $(BASE_TAG)

## IMAGE: filesystem
FILESYSTEM_TAG = $(shell $(GET_TAG) filesystem)
filesystem:
	cd src && docker build  --build-arg ARCH=${ARCH}  --build-arg BASE_TAG=$(BASE_TAG) -t $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG) . -f filesystem/Dockerfile
run-filesystem: /tmp/cocalc/done
	rm -rf /tmp/filesystem && mkdir /tmp/filesystem && chmod a+rwx /tmp/filesystem && docker run --name run-filesystem -it --rm -v /tmp/filesystem:/data -v /tmp/cocalc:/cocalc $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG)
push-filesystem:
	docker push $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG)
assemble-filesystem:
	./src/scripts/assemble.sh $(DOCKER_USER)/filesystem $(FILESYSTEM_TAG)

## IMAGE: storage
STORAGE_TAG = $(shell $(GET_TAG) storage)

# JFS_VERSION from https://github.com/juicedata/juicefs/tags
JFS_VERSION=1.2.0-beta1
# See https://github.com/GoogleCloudPlatform/gcsfuse/tags
GCSFUSE_VERSION=2.2.0
# See https://github.com/Snapchat/KeyDB/releases
KEYDB_VERSION=6.3.4
storage:
	cd src/storage && docker build  --build-arg ARCH=$(ARCH) --build-arg ARCH1=$(ARCH1) --build-arg ARCH=$(ARCH)  --build-arg JFS_VERSION=$(JFS_VERSION)  --build-arg KEYDB_VERSION=$(KEYDB_VERSION) --build-arg GCSFUSE_VERSION=$(GCSFUSE_VERSION) --build-arg BASE_TAG=$(BASE_TAG) -t $(DOCKER_USER)/storage$(ARCH):$(STORAGE_TAG) .
run-storage:
	docker run --name run-storage -it --rm $(DOCKER_USER)/storage$(ARCH):$(STORAGE_TAG) bash
push-storage:
	docker push $(DOCKER_USER)/storage$(ARCH):$(STORAGE_TAG)
assemble-storage:
	./src/scripts/assemble.sh $(DOCKER_USER)/storage $(STORAGE_TAG)


VPN_TAG = $(shell $(GET_TAG) vpn)
vpn:
	cd src/vpn && docker build  -t $(DOCKER_USER)/vpn$(ARCH):$(VPN_TAG) .
run-vpn:
	docker run --name run-vpn -it --rm $(DOCKER_USER)/vpn$(ARCH):$(VPN_TAG) bash
push-vpn:
	docker push $(DOCKER_USER)/vpn$(ARCH):$(VPN_TAG)
assemble-vpn:
	./src/scripts/assemble.sh $(DOCKER_USER)/vpn $(VPN_TAG)


## IMAGE: compute
COMPUTE_TAG = $(shell $(GET_TAG) compute)
compute:
	cd src && docker build --build-arg ARCH=${ARCH} --build-arg BASE_TAG=$(BASE_TAG)  -t $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG) . -f compute/Dockerfile
run-compute: /tmp/cocalc/done
	docker run --name run-compute -v /tmp/cocalc:/cocalc -it --network=host --rm $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG)
push-compute:
	docker push $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG)
assemble-compute:
	./src/scripts/assemble.sh $(DOCKER_USER)/compute $(COMPUTE_TAG)



## IMAGE: python
PYTHON_TAG = $(shell $(GET_TAG) python)
python:
	cd src/python && docker build --build-arg ARCH=${ARCH} --build-arg COMPUTE_TAG=$(COMPUTE_TAG)  -t $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG) .
run-python:
	docker run --name run-python --network=host -it --rm $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG) bash
push-python:
	docker push $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG)
assemble-python:
	./src/scripts/assemble.sh $(DOCKER_USER)/python $(PYTHON_TAG)

## IMAGE: microk8s -- kubernetes via microk8s
## This is the non-gpu version, which supports x86 and arm
## We should also have a GPU version with more packages that supports only x86.
MICROK8S_TAG = $(shell $(GET_TAG) microk8s)
microk8s:
	cd src && docker build  --build-arg ARCH=${ARCH} --build-arg COMPUTE_TAG=$(COMPUTE_TAG)  -t $(DOCKER_USER)/microk8s$(ARCH):$(MICROK8S_TAG) . -f microk8s/Dockerfile
run-microk8s:
	docker run --name run-microk8s --network=host -it --rm $(DOCKER_USER)/microk8s$(ARCH):$(MICROK8S_TAG)
push-microk8s:
	docker push $(DOCKER_USER)/microk8s$(ARCH):$(MICROK8S_TAG)
assemble-microk8s:
	./src/scripts/assemble.sh $(DOCKER_USER)/microk8s $(MICROK8S_TAG)

## IMAGE: jupyterhub
/tmp/cocalc-jupyterhub/done: /tmp/cocalc/done
	rm -rf /tmp/cocalc-jupyterhub
	cp -ar /tmp/cocalc /tmp/cocalc-jupyterhub
	rm -f /tmp/cocalc-jupyterhub/done
	node -e "const data = require('fs').readFileSync('images.json'); const json = JSON.parse(data); console.log(JSON.stringify(json.jupyterhub.proxy,0,2));" > /tmp/cocalc-openwebui/conf/proxy.json
	touch /tmp/cocalc-jupyterhub/done

JUPYTERHUB_TAG = $(shell $(GET_TAG) jupyterhub)
jupyterhub:
	cd src/jupyterhub && docker build  --build-arg ARCH=${ARCH} --build-arg MICROK8S_TAG=$(MICROK8S_TAG)  -t $(DOCKER_USER)/jupyterhub$(ARCH):$(JUPYTERHUB_TAG) .
run-jupyterhub: /tmp/cocalc-jupyterhub/done
	docker run -v /tmp/cocalc-jupyterhub/:/cocalc -v /data/.cache/.kube:/home/user/.kube --name run-jupyterhub --network=host -it --rm $(DOCKER_USER)/jupyterhub$(ARCH):$(JUPYTERHUB_TAG)
push-jupyterhub:
	docker push $(DOCKER_USER)/jupyterhub$(ARCH):$(JUPYTERHUB_TAG)
assemble-jupyterhub:
	./src/scripts/assemble.sh $(DOCKER_USER)/jupyterhub $(JUPYTERHUB_TAG)


# The http proxy Docker image.  We build this and use it in Kubernetes
# to expose one or more services, while providing a registration token
# and ssl.  It isn't an image directly, but something that is used
# in Kubernetes (or maybe docker-compose?).
PROXY_TAG = $(shell $(GET_TAG) proxy)
proxy:
	cd src/proxy && docker build -t $(DOCKER_USER)/proxy$(ARCH):$(PROXY_TAG) .
run-proxy:
	docker run --name run-proxy -it --network=host --rm $(DOCKER_USER)/proxy$(ARCH):$(PROXY_TAG)
push-proxy:
	docker push $(DOCKER_USER)/proxy$(ARCH):$(PROXY_TAG)
assemble-proxy:
	./src/scripts/assemble.sh $(DOCKER_USER)/proxy $(PROXY_TAG)
	./src/scripts/assemble.sh $(DOCKER_USER)/proxy $(PROXY_TAG) latest

# This is separate from the Docker image. You also must manually maintain
# the version in package.json.
publish-proxy-npm:
	cd src/proxy/src && pnpm publish --no-git-checks


## IMAGE: openwebui
OPENWEBUI_TAG=$(shell $(GET_TAG) openwebui)
PROXY_VERSION=1.3.0
/tmp/cocalc-openwebui/done: /tmp/cocalc/done
	rm -rf /tmp/cocalc-openwebui
	cp -ar /tmp/cocalc /tmp/cocalc-openwebui
	rm -f /tmp/cocalc-openwebui/done
	node -e "const data = require('fs').readFileSync('images.json'); const json = JSON.parse(data); console.log(JSON.stringify(json.openwebui.proxy,0,2));" > /tmp/cocalc-openwebui/conf/proxy.json
	touch /tmp/cocalc-openwebui/done

openwebui:
	cd src/openwebui && docker build --build-arg PROXY_VERSION=${PROXY_VERSION} --build-arg ARCH=${ARCH} --build-arg COMPUTE_TAG=$(COMPUTE_TAG) --build-arg ARCH1=$(ARCH1) -t $(DOCKER_USER)/openwebui$(ARCH):$(OPENWEBUI_TAG) .
run-openwebui:  /tmp/cocalc-openwebui/done
	docker run -v /tmp/cocalc-openwebui/:/cocalc --name run-openwebui --gpus all -it --rm --privileged -v /var/run/docker.sock:/var/run/docker.sock --network=host $(DOCKER_USER)/openwebui$(ARCH):$(OPENWEBUI_TAG)
run-openwebui-nogpu: /tmp/cocalc-openwebui/done
	docker run -v /tmp/cocalc-openwebui:/cocalc --name run-openwebui-nogpu -it --rm --network=host --privileged -v /var/run/docker.sock:/var/run/docker.sock  $(DOCKER_USER)/openwebui$(ARCH):$(OPENWEBUI_TAG)
push-openwebui:
	docker push $(DOCKER_USER)/openwebui$(ARCH):$(OPENWEBUI_TAG)
assemble-openwebui:
	./src/scripts/assemble.sh $(DOCKER_USER)/openwebui $(OPENWEBUI_TAG)


math:
	make rstats && make julia && make lean
push-math:
	make push-rstats && make push-julia && make push-lean
assemble-math:
	make assemble-rstats && make assemble-julia && make assemble-lean

## Helpful build artifact: sagemath-core -- this is just used for convenience
## so we don't have to build sage repeatedly

# This takes a long time to run (e.g., hours!), since it **builds sage from source**.
# You only ever should do this once per Sage release and architecture.  It results
# in a directory /usr/local/sage, which gets copied into
# the sagemath image below.  Run this on both an x86 and arm64 machine, then run
# sagemath-core to combine the two docker images together.
SAGEMATH_VERSION=$(shell $(GET_VERSION) sagemath)
SAGEMATH_TAG=$(shell $(GET_TAG) sagemath)
sagemath-core:
	cd src/sagemath && docker build --build-arg SAGEMATH_VERSION=${SAGEMATH_VERSION} -t $(DOCKER_USER)/sagemath-core$(ARCH):$(SAGEMATH_TAG) -f core/Dockerfile .
run-sagemath-core:
	docker run --name run-sagemath-core --network=host -it --rm $(DOCKER_USER)/sagemath-core$(ARCH):$(SAGEMATH_TAG) bash
push-sagemath-core:
	docker push $(DOCKER_USER)/sagemath-core$(ARCH):$(SAGEMATH_TAG)
assemble-sagemath-core:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-core $(SAGEMATH_TAG) $(SAGEMATH_TAG)
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-core $(SAGEMATH_TAG) latest


## IMAGE: sagemath
# this depends on sagemath-core existing locally
sagemath:
	cd src/sagemath && \
	docker build  --build-arg PYTHON_TAG=$(PYTHON_TAG) --build-arg SAGEMATH_VARIANT="core" --build-arg ARCH=${ARCH} --build-arg SAGEMATH_VERSION=$(SAGEMATH_VERSION)  -t $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION) -f Dockerfile .
run-sagemath:
	docker run --name run-sagemath --network=host -it --rm $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION) bash
push-sagemath:
	docker push $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION)
assemble-sagemath:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath $(SAGEMATH_VERSION)


## Helpful build artifact: sagemath-optional -- this is just used for convenience
## so we don't have to build sage optional packages repeatedly

SAGEMATH_VERSION=$(shell $(GET_VERSION) sagemath)
SAGEMATH_TAG=$(shell $(GET_TAG) sagemath)
sagemath-optional:
	cd src/sagemath && docker build --build-arg ARCH=${ARCH} --build-arg SAGEMATH_VERSION=${SAGEMATH_VERSION} --build-arg PYTHON_TAG=$(PYTHON_TAG) -t $(DOCKER_USER)/sagemath-optional$(ARCH):$(SAGEMATH_TAG) -f optional/Dockerfile${ARCH0} .
run-sagemath-optional:
	docker run --name run-sagemath-optional --network=host -it --rm $(DOCKER_USER)/sagemath-optional$(ARCH):$(SAGEMATH_TAG) bash
push-sagemath-optional:
	docker push $(DOCKER_USER)/sagemath-optional$(ARCH):$(SAGEMATH_TAG)
assemble-sagemath-optional:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-optional $(SAGEMATH_TAG) $(SAGEMATH_TAG)
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-optional $(SAGEMATH_TAG) latest


## IMAGE: sagemathopt
# this depends on sagemath-optional existing locally
sagemathopt:
	cd src/sagemath && \
	docker build  --build-arg SAGEMATH_VARIANT="optional" --build-arg ARCH=${ARCH} --build-arg SAGEMATH_VERSION=$(SAGEMATH_VERSION) -t $(DOCKER_USER)/sagemathopt$(ARCH):$(SAGEMATH_VERSION) -f Dockerfile .
run-sagemathopt:
	docker run --name run-sagemathopt --network=host -it --rm $(DOCKER_USER)/sagemathopt$(ARCH):$(SAGEMATH_VERSION) bash
push-sagemathopt:
	docker push $(DOCKER_USER)/sagemathopt$(ARCH):$(SAGEMATH_VERSION)
assemble-sagemathopt:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemathopt $(SAGEMATH_VERSION)


## NOTE USED YET -- not clear it is useful
# This is very similar to sagemath-core, but much bigger, since it doesn't delete
# any build artifacts or strip anything. The result is meant to be suitable for
# immediately doing sage development and installing optional packages, etc.
SAGEMATHDEV_VERSION=$(shell $(GET_VERSION) sagemath)
SAGEMATHDEV_TAG=$(shell $(GET_TAG) sagemath)
sagemath-dev:
	cd src/sagemath && docker build --build-arg SAGEMATH_VERSION=${SAGEMATHDEV_VERSION} -t $(DOCKER_USER)/sagemath-dev$(ARCH):$(SAGEMATHDEV_TAG) -f dev/Dockerfile .
run-sagemath-dev:
	docker run  --name run-sagemath-dev --network=host -it --rm $(DOCKER_USER)/sagemath-dev$(ARCH):$(SAGEMATHDEV_TAG) bash
push-sagemath-dev:
	docker push $(DOCKER_USER)/sagemath-dev$(ARCH):$(SAGEMATHDEV_TAG)
assemble-sagemath-dev:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-dev $(SAGEMATHDEV_TAG) $(SAGEMATHDEV_TAG)
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-dev $(SAGEMATHDEV_TAG) latest




## IMAGE: julia

# See https://julialang.org/downloads/ for current version
JULIA_VERSION=$(shell $(GET_VERSION) julia)
JULIA_TAG=$(shell $(GET_TAG) julia)
julia:
	cd src/julia && docker build --build-arg PYTHON_TAG=$(PYTHON_TAG) --build-arg ARCH=${ARCH} --build-arg JULIA_VERSION=$(JULIA_VERSION) -t $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG) .
run-julia:
	docker run  --name run-julia --network=host -it --rm $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG) bash
push-julia:
	docker push $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG)
assemble-julia:
	./src/scripts/assemble.sh $(DOCKER_USER)/julia $(JULIA_TAG)

## IMAGE: rstats
/tmp/cocalc-rstats/done: /tmp/cocalc/done
	rm -rf /tmp/cocalc-rstats
	cp -ar /tmp/cocalc /tmp/cocalc-rstats
	rm -f /tmp/cocalc-rstats/done
	node -e "const data = require('fs').readFileSync('images.json'); const json = JSON.parse(data); console.log(JSON.stringify(json.rstats.proxy,0,2));" > /tmp/cocalc-rstats/conf/proxy.json
	touch /tmp/cocalc-rstats/done

# See https://docs.posit.co/resources/install-r-source/#install-required-dependencies
# NOTE: I tried using just "r" for this docker image and everything works until trying
# to make thee assembled multiplatform package sagemathinc/r, where we just get a
# weird permission denied error.  I guess 1-letter docker images have issues.
R_VERSION=$(shell $(GET_VERSION) rstats)
R_TAG=$(shell $(GET_TAG) rstats)
rstats:
	cd src/rstats && docker build  --build-arg ARCH=${ARCH} --build-arg ARCH1=${ARCH1}  --build-arg PYTHON_TAG=$(PYTHON_TAG) --build-arg R_VERSION=$(R_VERSION) -t $(DOCKER_USER)/rstats$(ARCH):$(R_TAG) .
push-rstats:
	docker push $(DOCKER_USER)/rstats$(ARCH):$(R_TAG)
run-rstats: /tmp/cocalc-rstats/done
	docker run  -v /tmp/cocalc-rstats/:/cocalc  --name run-rstats  -it --rm --network=host $(DOCKER_USER)/rstats$(ARCH):$(R_TAG)
assemble-rstats:
	./src/scripts/assemble.sh $(DOCKER_USER)/rstats $(R_TAG)


## IMAGE: anaconda
ANACONDA_TAG=$(shell $(GET_TAG) anaconda)
anaconda:
	cd src/anaconda && docker build  --build-arg ARCH=${ARCH}  --build-arg COMPUTE_TAG=$(COMPUTE_TAG) -t $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG) .
push-anaconda:
	docker push $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG)
run-anaconda:
	docker run  --name run-anaconda --network=host -it --rm $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG)
assemble-anaconda:
	./src/scripts/assemble.sh $(DOCKER_USER)/anaconda $(ANACONDA_TAG)


## IMAGE: lean theorem prover
LEAN_TAG=$(shell $(GET_TAG) lean)
lean:
	cd src/lean && docker build  --build-arg ARCH=${ARCH}  --build-arg COMPUTE_TAG=$(COMPUTE_TAG) -t $(DOCKER_USER)/lean$(ARCH):$(LEAN_TAG) .
push-lean:
	docker push $(DOCKER_USER)/lean$(ARCH):$(LEAN_TAG)
run-lean: /tmp/cocalc/done
	docker run  -v /tmp/cocalc:/cocalc --network=host --name run-lean  -it --rm $(DOCKER_USER)/lean$(ARCH):$(LEAN_TAG)
assemble-lean:
	./src/scripts/assemble.sh $(DOCKER_USER)/lean $(LEAN_TAG)


# This is obviously x86 only:

HPC_VERSION=$(shell $(GET_VERSION) hpc)
HPC_TAG=$(shell $(GET_TAG) hpc)
hpc:
	cd src/hpc && docker build --build-arg ARCH=${ARCH}  --build-arg PYTHON_TAG=$(PYTHON_TAG) -t $(DOCKER_USER)/hpc:$(HPC_TAG) .
push-hpc:
	docker push $(DOCKER_USER)/hpc:$(HPC_TAG)
run-hpc: /tmp/cocalc/done
	docker run  --name run-hpc -v /tmp/cocalc:/cocalc -it --network=host --rm $(DOCKER_USER)/hpc:$(HPC_TAG)



#####
# GPU only images below
# Only need to worry about x86_64 for this, obviously:
#####
gpu:
	make cuda && make pytorch && make tensorflow && make colab
push-gpu:
	make push-cuda && make push-pytorch && make push-tensorflow && make push-colab


# See
#   https://gitlab.com/nvidia/container-images/cuda/blob/master/doc/supported-tags.md
# for the available supported versions.
CUDA_VERSION=$(shell $(GET_VERSION) cuda)
CUDA_TAG=$(shell $(GET_TAG) cuda)
cuda:
	cd src && docker build --build-arg CUDA_VERSION=$(CUDA_VERSION) -t $(DOCKER_USER)/cuda:$(CUDA_TAG) . -f cuda/Dockerfile
push-cuda:
	docker push $(DOCKER_USER)/cuda:$(CUDA_TAG)
run-cuda:
	docker run --name run-cuda --gpus all -it --network=host --rm $(DOCKER_USER)/cuda:$(CUDA_TAG) bash
run-cuda-nogpu:
	docker run  --name run-cuda-nogpu  -it --network=host --rm $(DOCKER_USER)/cuda:$(CUDA_TAG) bash

PYTORCH_VERSION=$(shell $(GET_VERSION) pytorch)
PYTORCH_TAG=$(shell $(GET_TAG) pytorch)
pytorch:
	cd src && docker build --build-arg PYTORCH_VERSION=$(PYTORCH_VERSION) -t $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) . -f pytorch/Dockerfile
push-pytorch:
	docker push $(DOCKER_USER)/pytorch:$(PYTORCH_TAG)
run-pytorch:
	docker run --name run-pytorch --gpus all -it --network=host --rm $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) bash
run-pytorch-nogpu:
	docker run --name run-pytorch-nogpu -it --rm $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) bash

# Fortunately nvcr.io/nvidia/tensorflow uses Ubuntu  too.
TENSORFLOW_VERSION=$(shell $(GET_VERSION) tensorflow)
TENSORFLOW_TAG=$(shell $(GET_TAG) tensorflow)
tensorflow:
	# do not cd to tensorflow directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	cd src && docker build  --build-arg TENSORFLOW_VERSION=$(TENSORFLOW_VERSION) -t $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) . -f tensorflow/Dockerfile
push-tensorflow:
	docker push $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG)
run-tensorflow:
	docker run --name run-tensorflow   --gpus all -it --network=host --rm $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) bash
run-tensorflow-nogpu:
	docker run --name run-tensorflow-nogpu -it --rm $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) bash

# They seem to do releases about once per month.
COLAB_VERSION=$(shell $(GET_VERSION) colab)
COLAB_TAG=$(shell $(GET_TAG) colab)
colab:
	cd src && docker build --build-arg COLAB_TAG=$(COLAB_VERSION) -t $(DOCKER_USER)/colab:$(COLAB_TAG) . -f colab/Dockerfile
push-colab:
	docker push $(DOCKER_USER)/colab:$(COLAB_TAG)
run-colab:
	docker run --name run-colab --gpus all -it --network=host --rm $(DOCKER_USER)/colab:$(COLAB_TAG) bash
run-colab-nogpu:
	docker run --name run-colab-nogpu -it --rm $(DOCKER_USER)/colab:$(COLAB_TAG) bash

# See
#   https://catalog.ngc.nvidia.com/orgs/nvidia/containers/jax/tags
# for the tag.
JAX_VERSION=$(shell $(GET_VERSION) jax)
JAX_TAG=$(shell $(GET_TAG) jax)
jax:
	# do not cd to jax directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	cd src && docker build  --build-arg JAX_VERSION=$(JAX_VERSION) -t $(DOCKER_USER)/jax:$(JAX_TAG) . -f jax/Dockerfile
push-jax:
	docker push $(DOCKER_USER)/jax:$(JAX_TAG)
run-jax:
	docker run --name run-jax --gpus all -it --network=host --rm $(DOCKER_USER)/jax:$(JAX_TAG) bash
run-jax-nogpu:
	docker run  --name run-jax-nogpu -it --rm $(DOCKER_USER)/jax:$(JAX_TAG) bash

