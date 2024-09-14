# Start with the first stage of the build.

ARG MYAPP_IMAGE=ubuntu:24.04
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
ENV PIP_ROOT_USER_ACTION=ignore

RUN rm /bin/sh && ln -s /bin/bash /bin/sh

COPY install-core-packages.sh /tmp/install-core-packages.sh
RUN /tmp/install-core-packages.sh && rm /tmp/install-core-packages.sh

COPY install-docker.sh /tmp/install-docker.sh
RUN /tmp/install-docker.sh && rm /tmp/install-docker.sh

COPY setup-user.sh /tmp/setup-user.sh
RUN /tmp/setup-user.sh && rm /tmp/setup-user.sh

RUN apt-get update && apt-get upgrade -y

# FOR DEV/TESTING ONLY
# Copy the cocalc directory -- this is going to usually be mounted
# from the host image to we instead always get an up to date version,
# but it's nice to have some version here for testing purposes.
# COPY --from=sagemathinc/compute-cocalc /cocalc /cocalc

COPY scripts/* /usr/local/bin/

USER user
