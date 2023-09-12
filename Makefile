# Docker image parameters
DOCKER_USER=sagemathinc
IMAGE_NAME=compute
IMAGE_TAG=latest
PLATFORMS=linux/amd64,linux/arm64

# Git parameters
BRANCH=master
COMMIT=$(shell git ls-remote -h https://github.com/sagemathinc/cocalc $(BRANCH) | awk '{print $$1}')

# Builder parameters
BUILDER_NAME=mybuilder

# If you need to customize the PATH in some setting:
# export PATH:=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Build a multi-platform Docker image
build:
	docker buildx build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH) --build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') --platform $(PLATFORMS) -t $(DOCKER_USER)/$(IMAGE_NAME):$(IMAGE_TAG) .

# Load the Docker image into local registry for testing
load:
	docker buildx build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH) --build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') -t $(DOCKER_USER)/$(IMAGE_NAME):$(IMAGE_TAG) --load .

# Push the Docker image to Docker Hub
push:
	docker buildx build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH) --build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ') --platform $(PLATFORMS) -t $(DOCKER_USER)/$(IMAGE_NAME):$(IMAGE_TAG) --push .

# Create a new builder instance
create-builder:
	docker buildx create --name $(BUILDER_NAME)

# Use the builder instance
use-builder:
	docker buildx use $(BUILDER_NAME)

# Inspect the builder instance
inspect-builder:
	docker buildx inspect --bootstrap

# Quicker local builds not using the multi-platform support.
# This is MUCH faster when you want to do development.  The above
# is for making a public release for linux/amd64 and linux/arm64.
compute:
	docker build --build-arg commit=$(COMMIT) --build-arg BRANCH=$(BRANCH) --build-arg BUILD_DATE=$(shell date -u +'%Y-%m-%dT%H:%M:%SZ')  -t $(DOCKER_USER)/$(IMAGE_NAME) .

python3:
	cd images/python3 && docker build -t $(DOCKER_USER)/compute-python3 .

build-python3:
	cd images/python3 && docker buildx build --platform $(PLATFORMS) -t $(DOCKER_USER)/compute-python3:$(IMAGE_TAG) .

push-python3:
	cd images/python3 && docker buildx build --platform $(PLATFORMS) -t $(DOCKER_USER)/compute-python3:$(IMAGE_TAG) --push .



#####
#####

# Only need to worry about x86_64 for this, obviously:
pytorch:
	cd images/pytorch && docker build -t $(DOCKER_USER)/compute-pytorch .

push-pytorch:
	cd images/pytorch && docker push $(DOCKER_USER)/compute-pytorch



# Only need to worry about x86_64 for this, obviously:
tensorflow:
	# do not cd to tensorflow directory, because we need to access start.js which is here.
	# We want the build context to be bigger.
	docker build -t  $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG) -f images/tensorflow/Dockerfile .

push-tensorflow:
	docker push $(DOCKER_USER)/compute-tensorflow:$(IMAGE_TAG)


