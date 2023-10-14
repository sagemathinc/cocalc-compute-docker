# Start with the first stage of the build.

ARG MYAPP_IMAGE=ubuntu:22.04
FROM $MYAPP_IMAGE AS build_image

MAINTAINER William Stein <wstein@sagemath.com>

USER root

# Setup environment variables.
USER root
ENV LC_ALL=C.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV TERM=screen
ENV DEBUG_CONSOLE=yes

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

# Install core tools
#  libfuse-dev is critical since the cocalc source assumes it is there.
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
       curl \
       fuse \
       libfuse-dev \
       neovim \
       sudo \
       python-is-python3

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

# Setup a normal user account (not root) that matches cocalc.com (so uid=gid=2001),
# give it passwordless root and ability to mount fuse filesystems.
# And to use docker without sudo.
RUN /usr/sbin/groupadd --gid=2001 -o user \
  && /usr/sbin/useradd  --home-dir=/home/user --gid=2001 --uid=2001 --shell=/bin/bash user \
  && mkdir -p /home/user &&  chown 2001:2001 -R /home/user \
  && echo '%user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers \
  && sed -i 's/#user_allow_other/user_allow_other/g' /etc/fuse.conf \
  && sed -i 's/docker:x:999:/docker:x:999:user/' /etc/group \
  && echo "[ -f /cocalc/nvm/nvm.sh ] && source /cocalc/nvm/nvm.sh" >> /etc/bash.bashrc
  
# FOR DEV/TESTING ONLY
# Copy the cocalc directory -- this is going to usually be mounted
# from the host image to we instead always get an up to date version, 
# but it's nice to have some version here for testing purposes.
# COPY --from=sagemathinc/compute-cocalc /cocalc /cocalc

COPY open /usr/bin/
RUN chmod a+rx /usr/bin/open

USER user
