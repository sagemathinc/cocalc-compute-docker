# See https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tensorflow for the tag.
# fortunately nvcr.io/nvidia/tensorflow uses Ubuntu 22.04LTS too.
FROM nvcr.io/nvidia/tensorflow:23.08-tf2-py3

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
       pkg-config

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
COPY --from=sagemathinc/compute /cocalc /cocalc

# The Nvidia image puts its own old nodejs install at the front
# of the path in both /etc/bash.bashrc and in /root/.bashrc
# That would break everything, since we want our node v18 as installed above.
RUN \
     grep -v nvm /root/.bashrc > /root/.bashrc.new \
  && mv /root/.bashrc.new /root/.bashrc \
     grep -v nvm /etc/bash.bashrc > /etc/bash.bashrc.new \
  && mv /etc/bash.bashrc.new /etc/bash.bashrc

COPY start.js /cocalc/src/compute/compute

ENV HOME /home/user

WORKDIR /home/user

CMD cd /cocalc/src/compute/compute && node start.js

