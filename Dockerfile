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
       tmux \
       flex \
       bison \
       libreadline-dev \
       poppler-utils \
       net-tools \
       wget \
       curl \
       git \
       python3 \
       python-is-python3 \
       python3-pip \
       make \
       g++ \
       sudo \
       psmisc \
       rsync \
       tidy \
       vim \
       inetutils-ping \
       lynx \
       telnet \
       git \
       ssh \
       m4 \
       latexmk \
       libpq5 \
       libpq-dev \
       build-essential \
       automake \
       jq \
       bsdmainutils \
       postgresql \
       nodejs \
       npm \
       libfuse-dev \
       pkg-config

RUN echo "umask 077" >> /etc/bash.bashrc

# Build a UTF-8 locale, so that tmux works -- see https://unix.stackexchange.com/questions/277909/updated-my-arch-linux-server-and-now-i-get-tmux-need-utf-8-locale-lc-ctype-bu
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

# Configuration

COPY login.defs /etc/login.defs
COPY login /etc/defaults/login
COPY run.py /root/run.py
COPY bashrc /root/.bashrc

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
RUN \
     umask 022 && git clone --depth=1 https://github.com/sagemathinc/cocalc.git \
  && cd /cocalc && git pull && git fetch -u origin $BRANCH:$BRANCH && git checkout ${commit:-HEAD}

RUN umask 022 && pip3 install --upgrade /cocalc/src/smc_pyutil/

# Install pnpm package manager that we now use instead of npm
RUN umask 022 \
  && npm install -g pnpm

# Build cocalc itself.
RUN umask 022 \
  && cd /cocalc/src \
  && npm run make

# And cleanup npm cache, which is several hundred megabytes after building cocalc above.
RUN rm -rf /root/.npm

CMD /root/run.py

ARG BUILD_DATE
LABEL org.label-schema.build-date=$BUILD_DATE

EXPOSE 22 80 443
