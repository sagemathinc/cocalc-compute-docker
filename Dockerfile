# Start with the first stage of the build.

ARG MYAPP_IMAGE=ubuntu:22.10
FROM $MYAPP_IMAGE AS build_image

MAINTAINER William Stein <wstein@sagemath.com>

USER root

# See https://github.com/sagemathinc/cocalc/issues/921
ENV LC_ALL C.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV TERM screen

# So we can source (see http://goo.gl/oBPi5G)
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Ubuntu software that are used by CoCalc (latex, pandoc, sage)
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
       git \
       curl \
       make \
       g++ \
       fuse \
       libfuse-dev \
       neovim \
       pkg-config

# Installing nodejs/npm from official Ubuntu brings in over 1GB
# of packages, whereas this is much smaller:
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y nodejs

# Get the commit to checkout and build:
ARG BRANCH=master
ARG commit=HEAD

# Pull latest source code for CoCalc and checkout requested commit (or HEAD)
RUN git clone --depth=1 https://github.com/sagemathinc/cocalc.git \
  && cd /cocalc && git pull && git fetch -u origin $BRANCH:$BRANCH && git checkout ${commit:-HEAD}

# Install pnpm package manager that we now use instead of npm
RUN npm install -g pnpm

# Copy over a custom workspace file, so pnpm ONLY installs packages, and builds, etc.
# the modules that actually are needed for @cocalc/compute. This makes a huge difference
# in size and speed.
COPY pnpm-workspace.yaml /cocalc/src/packages/pnpm-workspace.yaml

# Install deps for the @cocalc/compute module
RUN cd /cocalc/src/packages && pnpm install

# Build
RUN cd /cocalc/src/packages && pnpm run -r build

# Delete packages that were only needed for the build.
# Deleting node_modules and isntalling is the recommended approach by pnpm.
RUN cd /cocalc/src/packages && rm -rf node_modules && pnpm install --prod

# Now, start the second stage.
FROM $MYAPP_IMAGE

# Setup environment variables.
USER root
ENV LC_ALL=C.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV TERM=screen

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
       curl \
       fuse \
       libfuse-dev \
       neovim \
       pkg-config

RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y nodejs

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the cocalc directory from the build image.
COPY --from=build_image /cocalc /cocalc

CMD sleep infinity

ARG BUILD_DATE
LABEL org.label-schema.build-date=$BUILD_DATE
