# Docker image parameters
DOCKER_USER=sagemathinc
IMAGE_TAG=latest

# CoCalc Git parameters
BRANCH=master

COMMIT=$(shell git ls-remote -h https://github.com/sagemathinc/cocalc $(BRANCH) | awk '{print $$1}')

ARCH0=$(shell uname -m | sed 's/x86_64/-x86_64/;s/arm64/-arm64/;s/aarch64/-arm64/')
# Depending on your platform, set the ARCH variable
ARCH=$(shell uname -m | sed 's/x86_64//;s/arm64/-arm64/;s/aarch64/-arm64/')

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

cocalc:
	cd src/cocalc && docker build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH)  -t $(DOCKER_USER)/compute-cocalc$(ARCH):$(IMAGE_TAG) .
run-cocalc:
	docker run -it --rm $(DOCKER_USER)/compute-cocalc$(ARCH):$(IMAGE_TAG) bash

# Copy from docker image and publish @cocalc/compute-cocalc$(ARCH)
# to the npm registry.  This only works, of course, if you are signed
# into npm as a user that can publish to @cocalc.
# This automatically publishes as the next available minor version of
# the package (but doesn't modify local git at all).
COCALC_NPM=src/cocalc-npm
push-cocalc:
	rm -rf /tmp/cocalc-npm$(ARCH)
	mkdir -p /tmp/cocalc-npm$(ARCH)/dist
	cp -rv $(COCALC_NPM)/* /tmp/cocalc-npm$(ARCH)
	docker rm temp-copy-cocalc || true
	docker create --name temp-copy-cocalc $(DOCKER_USER)/compute-cocalc$(ARCH)
	docker cp temp-copy-cocalc:/cocalc /tmp/cocalc-npm$(ARCH)/dist/cocalc
	docker rm temp-copy-cocalc
	cd /tmp/cocalc-npm$(ARCH)/dist/ && tar -zcf cocalc.tar.gz cocalc
	rm -r /tmp/cocalc-npm$(ARCH)/dist/cocalc/
	# Add -arm64 extension to package name, if necessary.
	@if [ -n "$(ARCH)" ]; then sed -i.bak 's/compute-server/compute-server-arm64/g' /tmp/cocalc-npm$(ARCH)/package.json; fi
	cd /tmp/cocalc-npm$(ARCH) \
		&& npm version `npm view @cocalc/compute-server$(ARCH) version` || true \
		&& npm version minor \
		&& npm publish --access=public --no-git-checks
	rm -rf /tmp/cocalc-npm$(ARCH)

build-compute-server-base-arch:
	cd src/base && docker build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH)  -t $(DOCKER_USER)/compute-server-base$(ARCH0):$(IMAGE_TAG) .
run-compute-server-base-arch:
	docker run -it --rm $(DOCKER_USER)/compute-server-base$(ARCH0):$(IMAGE_TAG) bash
push-compute-server-base-arch:
	docker push $(DOCKER_USER)/compute-server-base$(ARCH0):$(IMAGE_TAG)
assemble-compute-server-base:
	./src/scripts/multiarch.sh $(DOCKER_USER)/compute-server-base $(IMAGE_TAG)

build-compute-server-filesystem-arch:
	cd src/filesystem && docker build -t $(DOCKER_USER)/compute-server-filesystem$(ARCH0):$(IMAGE_TAG) .
run-compute-server-filesystem-arch:
	docker run -it --rm $(DOCKER_USER)/compute-server-filesystem$(ARCH0):$(IMAGE_TAG) bash
push-compute-server-filesystem-arch:
	docker push $(DOCKER_USER)/compute-server-filesystem$(ARCH0):$(IMAGE_TAG)
assemble-compute-server-filesystem:
	./src/scripts/multiarch.sh $(DOCKER_USER)/compute-server-filesystem $(IMAGE_TAG)

compute:
	cd src/compute && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute$(ARCH):$(IMAGE_TAG) .

python:
	cd src/python && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG) .
push-python:
	docker push $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG)
run-python:
	docker run -it --rm $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG) bash


math:
	make sagemath-10.1 && make rlang && make anaconda && make julia
push-math:
	make push-sagemath-10.1 && make push-rlang && make push-anaconda && make push-julia

# This takes a long time to run, since it builds sage from source.  You only ever should do this once per
# Sage release and architecture.  It results in a directory /usr/local/sage, which gets copied into
# the sagemath-10.1 image below.  Run this on both an x86 and arm64 machine, then run
# sagemath-10.1-core to combine the two docker images together.
sagemath-10.1-core-arch:
	cd src/sagemath-10.1/core && docker build  -t $(DOCKER_USER)/sagemath-10.1-core$(ARCH0):$(IMAGE_TAG) .
push-sagemath-10.1-core-arch:
	docker push $(DOCKER_USER)/sagemath-10.1-core$(ARCH0):$(IMAGE_TAG)
run-sagemath-10.1-core-arch:
	docker run -it --rm $(DOCKER_USER)/sagemath-10.1-core$(ARCH0):$(IMAGE_TAG) bash
# Run this *after* sagemath-10.1-core-arch has been run on both x86_64 *and* on arm64.
sagemath-10.1-core:
	./src/scripts/multiarch.sh $(DOCKER_USER)/sagemath-10.1-core $(IMAGE_TAG)
run-sagemath-10.1-core:
	docker run -it --rm $(DOCKER_USER)/sagemath-10.1-core:$(IMAGE_TAG) bash

# this depends on sagemath-10.1-core having been built
sagemath-10.1-arch:
	cd src/sagemath-10.1 && \
	docker build -t $(DOCKER_USER)/sagemath-10.1$(ARCH0):$(IMAGE_TAG) -f Dockerfile .
push-sagemath-10.1-arch:
	docker push $(DOCKER_USER)/sagemath-10.1$(ARCH0):$(IMAGE_TAG)
run-sagemath-10.1-arch:
	docker run -it --rm $(DOCKER_USER)/sagemath-10.1$(ARCH0):$(IMAGE_TAG) bash
sagemath-10.0:
	./src/scripts/multiarch.sh $(DOCKER_USER)/sagemath-10.1 $(IMAGE_TAG)

julia:
	cd src/julia && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-julia$(ARCH):$(IMAGE_TAG) .
push-julia:
	docker push $(DOCKER_USER)/compute-julia$(ARCH):$(IMAGE_TAG)
run-julia:
	docker run -it --rm $(DOCKER_USER)/compute-julia$(ARCH):$(IMAGE_TAG) bash

rlang:
	cd src/rlang && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-rlang$(ARCH):$(IMAGE_TAG) .
push-rlang:
	docker push $(DOCKER_USER)/compute-rlang$(ARCH):$(IMAGE_TAG)
run-rlang:
	docker run -it --rm $(DOCKER_USER)/compute-rlang$(ARCH):$(IMAGE_TAG) bash

anaconda:
	cd src/anaconda && docker build  --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-anaconda$(ARCH):$(IMAGE_TAG) .
push-anaconda:
	docker push $(DOCKER_USER)/compute-anaconda$(ARCH):$(IMAGE_TAG)
run-anaconda:
	docker run -it --rm $(DOCKER_USER)/compute-anaconda$(ARCH):$(IMAGE_TAG) bash


#####
# GPU only images below
# Only need to worry about x86_64 for this, obviously:
#####
gpu:
	make cuda && make pytorch && make tensorflow && make colab
push-gpu:
	make push-cuda && make push-pytorch && make push-tensorflow && make push-colab

cuda:
	cd src/cuda && docker build -t $(DOCKER_USER)/compute-cuda:$(IMAGE_TAG) .
push-cuda:
	docker push $(DOCKER_USER)/compute-cuda:$(IMAGE_TAG)
run-cuda:
	docker run -it --rm $(DOCKER_USER)/compute-cuda$(ARCH):$(IMAGE_TAG) bash


pytorch:
	cd src/pytorch && docker build -t $(DOCKER_USER)/compute-pytorch:$(IMAGE_TAG) .
push-pytorch:
	docker push $(DOCKER_USER)/compute-pytorch:$(IMAGE_TAG)
run-pytorch:
	docker run -it --rm $(DOCKER_USER)/compute-pytorch$(ARCH):$(IMAGE_TAG) bash


tensorflow:
	# do not cd to tensorflow directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	cd src/tensorflow && docker build -t $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG) .
push-tensorflow:
	docker push $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG)
run-tensorflow:
	docker run -it --rm $(DOCKER_USER)/compute-tensorflow$(ARCH):$(IMAGE_TAG) bash


colab:
	cd src/colab && docker build -t $(DOCKER_USER)/compute-colab:$(IMAGE_TAG) .
push-colab:
	docker push $(DOCKER_USER)/compute-colab:$(IMAGE_TAG)
run-colab:
	docker run -it --rm $(DOCKER_USER)/compute-colab:$(IMAGE_TAG) bash




# # Everything for deep learning: tensorflow + pytorch + transformers all in one
# deeplearning:
# 	cd src/deeplearning && docker build -t $(DOCKER_USER)/compute-deeplearning:$(IMAGE_TAG) .
# push-deeplearning:
# 	docker push $(DOCKER_USER)/compute-deeplearning:$(IMAGE_TAG)
# run-deeplearning:
# 	docker run -it --rm $(DOCKER_USER)/compute-deeplearning$(ARCH):$(IMAGE_TAG) bash
