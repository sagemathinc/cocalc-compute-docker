# Docker image parameters
DOCKER_USER=sagemathinc
IMAGE_TAG=latest

# CoCalc Git parameters

BRANCH=compute  # not master right now while under dev!

COMMIT=$(shell git ls-remote -h https://github.com/sagemathinc/cocalc $(BRANCH) | awk '{print $$1}')
# Depending on your platform, set the ARCH variable
ARCH=$(shell uname -m | sed 's/x86_64//;s/arm64/-arm64/;s/aarch64/-arm64/')

core:
	make base && make filesystem && make manager && make python

push:
	make push-base && make push-filesystem && make push-manager && make push-python

base:
	cd src/base && docker build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH)  -t $(DOCKER_USER)/compute-base$(ARCH):$(IMAGE_TAG) .
push-base:
	docker push $(DOCKER_USER)/compute-base$(ARCH):$(IMAGE_TAG)

filesystem:
	cd src/filesystem && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-filesystem$(ARCH):$(IMAGE_TAG) .
push-filesystem:
	docker push $(DOCKER_USER)/compute-filesystem$(ARCH):$(IMAGE_TAG)

manager:
	cd src/manager && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-manager$(ARCH):$(IMAGE_TAG) .
push-manager:
	docker push $(DOCKER_USER)/compute-manager$(ARCH):$(IMAGE_TAG)


python:
	cd src/python && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG) .
push-python:
	docker push $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG)
run-python:
	docker run -it --rm $(DOCKER_USER)/compute-python$(ARCH):$(IMAGE_TAG) bash

sagemath-10.1:
	cd src/sagemath-10.1 && docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-sagemath-10.1$(ARCH):$(IMAGE_TAG) .
push-sagemath-10.1:
	docker push $(DOCKER_USER)/compute-sagemath-10.1$(ARCH):$(IMAGE_TAG)
run-sagemath-10.1:
	docker run -it --rm $(DOCKER_USER)/compute-sagemath-10.1$(ARCH):$(IMAGE_TAG) bash


#####
# GPU only images below
# Only need to worry about x86_64 for this, obviously:
#####

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



