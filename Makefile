# Docker image parameters
DOCKER_USER=sagemathinc
IMAGE_TAG=latest

# CoCalc Git parameters
BRANCH=master
COMMIT=$(shell git ls-remote -h https://github.com/sagemathinc/cocalc $(BRANCH) | awk '{print $$1}')
# Depending on your platform, set the ARCH variable
ARCH=$(shell uname -m | sed 's/x86_64//;s/aarch64/-arm64/')

base:
	cd src/base && time docker build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH)  -t $(DOCKER_USER)/compute$(ARCH):$(IMAGE_TAG)  .

push-base:
	time docker push $(DOCKER_USER)/compute$(ARCH):$(IMAGE_TAG)

python3:
	cd src/python3 && time docker build --build-arg ARCH=$(ARCH) -t $(DOCKER_USER)/compute-python3$(ARCH):$(IMAGE_TAG) .

push-python3:
	time docker push $(DOCKER_USER)/compute-python3$(ARCH):$(IMAGE_TAG)


#####
# GPU only images below
# Only need to worry about x86_64 for this, obviously:
#####

cuda:
	cd src/cuda && time docker build -t $(DOCKER_USER)/compute-cuda:$(IMAGE_TAG) .

push-cuda:
	time docker push $(DOCKER_USER)/compute-cuda:$(IMAGE_TAG)


pytorch:
	cd src/pytorch && time docker build -t $(DOCKER_USER)/compute-pytorch:$(IMAGE_TAG) .

push-pytorch:
	time docker push $(DOCKER_USER)/compute-pytorch:$(IMAGE_TAG)


tensorflow:
	# do not cd to tensorflow directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	cd src/tensorflow && time docker build -t $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG) .

push-tensorflow:
	docker push $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG)

