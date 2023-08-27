ARG MYAPP_IMAGE=ubuntu:22.10
FROM $MYAPP_IMAGE

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
       software-properties-common \
       git \
       build-essential \
       python3 \
       nodejs \
       npm \
       libfuse-dev \
       pkg-config

# The Jupyter kernel that gets auto-installed with some other jupyter Ubuntu packages
# doesn't have some nice options regarding inline matplotlib (and possibly others), so
# we delete it.
RUN rm -rf /usr/share/jupyter/kernels/python3

# Create this user, since the startup scripts assumes it exists, and user might install sage later.
RUN    adduser --quiet --shell /bin/bash --gecos "Sage user,101,," --disabled-password sage \
    && chown -R sage:sage /home/sage/

# Commit to checkout and build.
ARG BRANCH=master
ARG commit=HEAD

# Pull latest source code for CoCalc and checkout requested commit (or HEAD),
# install our Python libraries globally, then remove cocalc.  We only need it
# for installing these Python libraries (TODO: move to pypi?).
RUN git clone --depth=1 https://github.com/sagemathinc/cocalc.git \
  && cd /cocalc && git pull && git fetch -u origin $BRANCH:$BRANCH && git checkout ${commit:-HEAD}

# Install pnpm package manager that we now use instead of npm
RUN npm install -g pnpm

# Install deps for the modules we need
RUN cd /cocalc/src && ./workspaces.py install --packages=api-client,backend,jupyter,sync,sync-client,util

# Build modules we need
RUN cd /cocalc/src && ./workspaces.py build --packages=api-client,backend,jupyter,sync,sync-client,util

# Build the compute package
RUN cd /cocalc/src/packages/compute/ && pnpm make

CMD sleep infinity

ARG BUILD_DATE
LABEL org.label-schema.build-date=$BUILD_DATE

