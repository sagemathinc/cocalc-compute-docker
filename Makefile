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

core:
	make cocalc && make base && make filesystem  & make python
push-core:
	make push-cocalc && make push-filesystem && make push-python

## IMAGE: cocalc

# This "cocalc" is the subset of the cocalc nodejs code
# needed to run cocalc directly on the compute server
# for supporting websocketfs mounting, terminals, and jupyter notebooks.
# We build a docker image on the build host, but then copy the files out
# there, compress them, and push them to npmjs.com!  This is never pushed
# to dockerhub, and docker is just used for convenience to make the build
# easier.  We push two packages to npm, one for each arch.
COCALC_TAG=devel
cocalc:
	cd src/cocalc && docker build --build-arg COMMIT=$(COMMIT) --build-arg BRANCH=$(BRANCH)  -t $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG) .

run-cocalc:
	docker run -it --rm $(DOCKER_USER)/compute-cocalc$(ARCH):$(COCALC_TAG) bash

# Copy from docker image and publish @cocalc/compute-cocalc$(ARCH)
# to the npm registry.  This only works, of course, if you are signed
# into npm as a user that can publish to @cocalc.
# This automatically publishes as the next available minor version of
# the package (but doesn't modify local git at all).
COCALC_NPM=src/cocalc-npm
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
		&& npm version `npm view @cocalc/compute-server$(ARCH0) version` || true \
		&& npm version minor \
		&& npm publish --access=public --no-git-checks --tag=$(COCALC_TAG)
	# Comment this line out if you want to do something by hand, like explicitly set the version number on npmjs.
	rm -rf /tmp/cocalc-npm$(ARCH0)

## IMAGE: base
# We build base-x86_64 and base-arm64.
# They are pushed to dockerhub.
# We also run the assemble target to create the multiplatform
#     $(DOCKER_USER)/base
# which is what gets used everywhere else.
# TODO: most other code doesn't use this base tag, but needs to. We're
# using latest until all the other containers use it properly.
BASE_TAG=1.0
base:
	cd src/base && docker build -t $(DOCKER_USER)/base$(ARCH):$(BASE_TAG) .
run-base:
	docker run -it --rm $(DOCKER_USER)/base$(ARCH):$(BASE_TAG) bash
push-base:
	docker push $(DOCKER_USER)/base$(ARCH):$(BASE_TAG)
assemble-base:
	./src/scripts/assemble.sh $(DOCKER_USER)/base $(BASE_TAG)

## IMAGE: filesystem
FILESYSTEM_TAG = $(shell $(GET_TAG) filesystem)
filesystem:
	cd src && docker build  --build-arg BASE_TAG=$(BASE_TAG) -t $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG) . -f filesystem/Dockerfile
run-filesystem:
	rm -rf /tmp/filesystem && mkdir /tmp/filesystem && chmod a+rwx /tmp/filesystem && docker run -it --rm -v /tmp/filesystem:/data -v /cocalc:/cocalc $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG)
push-filesystem:
	docker push $(DOCKER_USER)/filesystem$(ARCH):$(FILESYSTEM_TAG)
assemble-filesystem:
	./src/scripts/assemble.sh $(DOCKER_USER)/filesystem $(FILESYSTEM_TAG)

## IMAGE: compute
COMPUTE_TAG = $(shell $(GET_TAG) compute)
compute:
	cd src && docker build --build-arg ARCH=${ARCH} --build-arg BASE_TAG=$(BASE_TAG)  -t $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG) . -f compute/Dockerfile
run-compute:
	docker run -it --rm $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG)
push-compute:
	docker push $(DOCKER_USER)/compute$(ARCH):$(COMPUTE_TAG)
assemble-compute:
	./src/scripts/assemble.sh $(DOCKER_USER)/compute $(COMPUTE_TAG)

## IMAGE: python
PYTHON_TAG = $(shell $(GET_TAG) python)
python:
	cd src/python && docker build --build-arg COMPUTE_TAG=$(COMPUTE_TAG)  -t $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG) .
run-python:
	docker run -it --rm $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG) bash
push-python:
	docker push $(DOCKER_USER)/python$(ARCH):$(PYTHON_TAG)
assemble-python:
	./src/scripts/assemble.sh $(DOCKER_USER)/python $(PYTHON_TAG)


## IMAGE: ollama
# See https://github.com/jmorganca/ollama/releases for versions
OLLAMA_VERSION=$(shell $(GET_VERSION) ollama)
OLLAMA_TAG=$(shell $(GET_TAG) ollama)
PROXY_VERSION=0.9.0
ollama:
	cd src/ollama && docker build --build-arg PROXY_VERSION=${PROXY_VERSION} --build-arg ARCH=${ARCH} --build-arg COMPUTE_TAG=$(COMPUTE_TAG) --build-arg ARCH1=$(ARCH1) --build-arg OLLAMA_VERSION=$(OLLAMA_VERSION) -t $(DOCKER_USER)/ollama$(ARCH):$(OLLAMA_TAG) .
run-ollama:
	docker run --gpus all -it --rm --network=host $(DOCKER_USER)/ollama$(ARCH):$(OLLAMA_TAG)
run-ollama-nogpu:
	docker run -it --rm --network=host $(DOCKER_USER)/ollama$(ARCH):$(OLLAMA_TAG)
push-ollama:
	docker push $(DOCKER_USER)/ollama$(ARCH):$(OLLAMA_TAG)
assemble-ollama:
	./src/scripts/assemble.sh $(DOCKER_USER)/ollama $(OLLAMA_TAG)


math:
	make sagemath && make rlang && make anaconda && make julia
push-math:
	make push-sagemath && make push-rlang && make push-anaconda && make push-julia

## IMAGE: sagemath-core

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
	docker run -it --rm $(DOCKER_USER)/sagemath-core$(ARCH):$(SAGEMATH_TAG) bash
push-sagemath-core:
	docker push $(DOCKER_USER)/sagemath-core$(ARCH):$(SAGEMATH_TAG)
assemble-sagemath-core:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-core $(SAGEMATH_TAG) $(SAGEMATH_TAG)
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath-core $(SAGEMATH_TAG) latest


## IMAGE: sagemath
# this depends on sagemath-core existing
sagemath:
	cd src/sagemath && \
	docker build  --build-arg ARCH=${ARCH} --build-arg SAGEMATH_VERSION=$(SAGEMATH_VERSION) -t $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION) -f Dockerfile .
run-sagemath:
	docker run -it --rm $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION) bash
push-sagemath:
	docker push $(DOCKER_USER)/sagemath$(ARCH):$(SAGEMATH_VERSION)
assemble-sagemath:
	./src/scripts/assemble.sh $(DOCKER_USER)/sagemath $(SAGEMATH_VERSION)


# This is very similar to sagemath-core, but much bigger, since it doesn't delete
# any build artifacts or strip anything. The result is meant to be suitable for
# immediately doing sage development and installing optional packages, etc.
SAGEMATHDEV_VERSION=$(shell $(GET_VERSION) sagemath)
SAGEMATHDEV_TAG=$(shell $(GET_TAG) sagemath)
sagemath-dev:
	cd src/sagemath && docker build --build-arg SAGEMATH_VERSION=${SAGEMATHDEV_VERSION} -t $(DOCKER_USER)/sagemath-dev$(ARCH):$(SAGEMATHDEV_TAG) -f dev/Dockerfile .
run-sagemath-dev:
	docker run -it --rm $(DOCKER_USER)/sagemath-dev$(ARCH):$(SAGEMATHDEV_TAG) bash
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
	cd src/julia && docker build  --build-arg ARCH=${ARCH} --build-arg JULIA_VERSION=$(JULIA_VERSION) -t $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG) .
run-julia:
	docker run -it --rm $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG) bash
push-julia:
	docker push $(DOCKER_USER)/julia$(ARCH):$(JULIA_TAG)
assemble-julia:
	./src/scripts/assemble.sh $(DOCKER_USER)/julia $(JULIA_TAG)

## IMAGE: rstats

# See https://docs.posit.co/resources/install-r-source/#install-required-dependencies
# NOTE: I tried using just "r" for this docker image and everything works until trying
# to make thee assembled multiplatform package sagemathinc/r, where we just get a
# weird permission denied error.  I guess 1-letter docker images have issues.
R_VERSION=$(shell $(GET_VERSION) rstats)
R_TAG=$(shell $(GET_TAG) rstats)
rstats:
	cd src/rstats && docker build  --build-arg ARCH=${ARCH} --build-arg R_VERSION=$(R_VERSION) -t $(DOCKER_USER)/rstats$(ARCH):$(R_TAG) .
push-rstats:
	docker push $(DOCKER_USER)/rstats$(ARCH):$(R_TAG)
run-rstats:
	docker run -it --rm $(DOCKER_USER)/rstats$(ARCH):$(R_TAG) bash
assemble-rstats:
	./src/scripts/assemble.sh $(DOCKER_USER)/rstats $(R_TAG)


## IMAGE: anaconda
ANACONDA_TAG=$(shell $(GET_TAG) anaconda)
anaconda:
	cd src/anaconda && docker build  --build-arg ARCH=${ARCH} -t $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG) .
push-anaconda:
	docker push $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG)
run-anaconda:
	docker run -it --rm $(DOCKER_USER)/anaconda$(ARCH):$(ANACONDA_TAG) bash
assemble-anaconda:
	./src/scripts/assemble.sh $(DOCKER_USER)/anaconda $(ANACONDA_TAG)


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
	docker run --gpus all -it --rm $(DOCKER_USER)/cuda:$(CUDA_TAG) bash
run-cuda-nogpu:
	docker run -it --rm $(DOCKER_USER)/cuda:$(CUDA_TAG) bash

PYTORCH_VERSION=$(shell $(GET_VERSION) pytorch)
PYTORCH_TAG=$(shell $(GET_TAG) pytorch)
pytorch:
	cd src && docker build --build-arg PYTORCH_VERSION=$(PYTORCH_VERSION) -t $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) . -f pytorch/Dockerfile
push-pytorch:
	docker push $(DOCKER_USER)/pytorch:$(PYTORCH_TAG)
run-pytorch:
	docker run --gpus all -it --rm $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) bash
run-pytorch-nogpu:
	docker run -it --rm $(DOCKER_USER)/pytorch:$(PYTORCH_TAG) bash

# Fortunately nvcr.io/nvidia/tensorflow uses Ubuntu 22.04LTS too.
TENSORFLOW_VERSION=$(shell $(GET_VERSION) tensorflow)
TENSORFLOW_TAG=$(shell $(GET_TAG) tensorflow)
tensorflow:
	# do not cd to tensorflow directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	cd src && docker build  --build-arg TENSORFLOW_VERSION=$(TENSORFLOW_VERSION) -t $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) . -f tensorflow/Dockerfile
push-tensorflow:
	docker push $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG)
run-tensorflow:
	docker run --gpus all -it --rm $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) bash
run-tensorflow-nogpu:
	docker run -it --rm $(DOCKER_USER)/tensorflow:$(TENSORFLOW_TAG) bash

# They seem to do releases about once per month.
COLAB_VERSION=$(shell $(GET_VERSION) colab)
COLAB_TAG=$(shell $(GET_TAG) colab)
colab:
	cd src && docker build --build-arg COLAB_TAG=$(COLAB_VERSION) -t $(DOCKER_USER)/colab:$(COLAB_TAG) . -f colab/Dockerfile
push-colab:
	docker push $(DOCKER_USER)/colab:$(COLAB_TAG)
run-colab:
	docker run --gpus all -it --rm $(DOCKER_USER)/colab:$(COLAB_TAG) bash
run-colab-nogpu:
	docker run -it --rm $(DOCKER_USER)/colab:$(COLAB_TAG) bash

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
	docker run --gpus all -it --rm $(DOCKER_USER)/jax:$(JAX_TAG) bash
run-jax-nogpu:
	docker run -it --rm $(DOCKER_USER)/jax:$(JAX_TAG) bash

