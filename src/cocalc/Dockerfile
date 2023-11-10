# Start with the first stage of the build.

ARG MYAPP_IMAGE=ubuntu:22.04
FROM $MYAPP_IMAGE AS build_image

MAINTAINER William Stein <wstein@sagemath.com>

USER root

# Ensure umask is 022 everywhere
RUN echo "umask 022" >> /etc/bash.bashrc

# See https://github.com/sagemathinc/cocalc/issues/921
ENV LC_ALL C.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV TERM screen

# So we can source (see http://goo.gl/oBPi5G)
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Ubuntu software
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

# Get the commit to checkout and build:
ARG BRANCH=master
ARG commit=HEAD

# Pull latest source code for CoCalc and checkout requested commit (or HEAD)
RUN git clone --depth=1 https://github.com/sagemathinc/cocalc.git \
  && cd /cocalc && git pull && git fetch -u origin $BRANCH:$BRANCH && git checkout ${commit:-HEAD}

RUN  mkdir -p /nvm \
  && cd /cocalc \
  && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | NVM_DIR=/nvm bash \
  && source /nvm/nvm.sh \
  && nvm install --no-progress 18.17.1 \
  && rm -rf /nvm/.git/ \
  && npm install -g npm pnpm \
  && echo "source /nvm/nvm.sh" >> /etc/bash.bashrc

# Copy over a custom workspace file, so pnpm ONLY installs packages, and builds, etc.
# the modules that actually are needed for @cocalc/compute.
# This makes a huge difference in size and speed.
COPY pnpm-workspace.yaml /cocalc/src/packages/pnpm-workspace.yaml
RUN chmod a+r /cocalc/src/packages/pnpm-workspace.yaml

# Install deps for the @cocalc/compute module
RUN . /nvm/nvm.sh && cd /cocalc/src/packages && pnpm install

# Build
RUN . /nvm/nvm.sh && cd /cocalc/src/packages && pnpm run -r build

# Install the @cocalc/compute module
RUN . /nvm/nvm.sh && cd /cocalc/src/compute && pnpm install

# And build it
RUN . /nvm/nvm.sh && cd /cocalc/src/compute && pnpm run -r build

# Delete packages that were only needed for the build.
# Deleting node_modules and installing is the recommended approach by pnpm.
RUN . /nvm/nvm.sh && cd /cocalc/src/packages && rm -rf node_modules && pnpm install --prod

RUN . /nvm/nvm.sh && cd /cocalc/src/compute && rm -rf node_modules && pnpm install --prod

RUN rm -rf /cocalc/.git

# 2-stage build to minimize wasted space
FROM $MYAPP_IMAGE

# Copy the cocalc directory from the build image.
COPY --from=build_image /cocalc /cocalc

COPY start-compute.js /cocalc/src/compute/compute
COPY start-filesystem.js /cocalc/src/compute/compute
COPY start-compute.sh /cocalc/
COPY start-filesystem.sh /cocalc/
COPY start-env.sh /cocalc/
COPY docker_pull.py /cocalc/
COPY disk_enlarger.py /cocalc/

RUN chmod a+rwx /cocalc/src/compute/compute/start*.js /cocalc/start*.sh /cocalc/*.py


