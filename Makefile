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

compute-python3:
	cd kernels/python3 && docker build -t sagemathinc/compute-python3 .

build-compute-python3:
	cd kernels/python3 && docker buildx build --platform $(PLATFORMS) -t $(DOCKER_USER)/compute-python3:$(IMAGE_TAG) .

push-compute-python3:
	cd kernels/python3 && docker buildx build --platform $(PLATFORMS) -t $(DOCKER_USER)/compute-python3:$(IMAGE_TAG) --push .
