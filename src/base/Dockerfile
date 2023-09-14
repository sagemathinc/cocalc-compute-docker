# Start with the first stage of the build.

ARG MYAPP_IMAGE=ubuntu:22.04
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

# Installing nodejs/npm from official Ubuntu brings in over 1GB
# of packages, whereas this is much smaller (and more up to date)
RUN  apt-get install -y ca-certificates curl gnupg \
  && mkdir -p /etc/apt/keyrings \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
  && export NODE_MAJOR=18 \
  && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
  && apt-get update && apt-get install nodejs -y

# Get the commit to checkout and build:
ARG BRANCH=master
ARG commit=HEAD

# Pull latest source code for CoCalc and checkout requested commit (or HEAD)
RUN git clone --depth=1 https://github.com/sagemathinc/cocalc.git \
  && cd /cocalc && git pull && git fetch -u origin $BRANCH:$BRANCH && git checkout ${commit:-HEAD}

# Install pnpm package manager that we now use instead of npm
RUN npm install -g pnpm

# Copy over a custom workspace file, so pnpm ONLY installs packages, and builds, etc.
# the modules that actually are needed for @cocalc/compute.
# This makes a huge difference in size and speed.
COPY pnpm-workspace.yaml /cocalc/src/packages/pnpm-workspace.yaml

# Install deps for the @cocalc/compute module
RUN cd /cocalc/src/packages && pnpm install

# Build
RUN cd /cocalc/src/packages && pnpm run -r build

# Install the @cocalc/compute module
RUN cd /cocalc/src/compute && pnpm install

# And build it
RUN cd /cocalc/src/compute && pnpm run -r build

# Delete packages that were only needed for the build.
# Deleting node_modules and isntalling is the recommended approach by pnpm.
RUN cd /cocalc/src/packages && rm -rf node_modules && pnpm install --prod

RUN cd /cocalc/src/compute && rm -rf node_modules && pnpm install --prod

# 2-stage build:
# Now, start the second stage.
FROM $MYAPP_IMAGE

# Setup environment variables.
USER root
ENV LC_ALL=C.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV TERM=screen
ENV DEBUG_CONSOLE=yes

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Install core tools and nodejs
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
       curl \
       fuse \
       libfuse-dev \
       neovim \
       pkg-config \
       sudo \
       make

RUN  apt-get install -y ca-certificates curl gnupg \
  && mkdir -p /etc/apt/keyrings \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
  && export NODE_MAJOR=18 \
  && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
  && apt-get update && apt-get install nodejs -y

# Install official upstream docker from docker.com, which is new and
# has the most features.
RUN \
     apt-get update -y \
  && apt-get install -y ca-certificates curl gnupg \
  && install -m 0755 -d /etc/apt/keyrings \
  && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg \
  && chmod a+r /etc/apt/keyrings/docker.gpg \
  && echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null \
  && apt-get update -y \
  && apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Copy the cocalc directory from the build image.
COPY --from=build_image /cocalc /cocalc

# Setup a normal user account (not root) that matches cocalc.com (so uid=gid=2001),
# give it passwordless root and ability to mount fuse filesystems.
# And to use docker without sudo.
RUN /usr/sbin/groupadd --gid=2001 -o user \
  && /usr/sbin/useradd  --home-dir=/home/user --gid=2001 --uid=2001 --shell=/bin/bash user \
  && mkdir -p /home/user &&  chown 2001:2001 -R /home/user \
  && echo '%user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && sed -i 's/#user_allow_other/user_allow_other/g' /etc/fuse.conf \
  && sed -i 's/docker:x:999:/docker:x:999:user/' /etc/group


COPY open /usr/bin/
