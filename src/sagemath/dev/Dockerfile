FROM ubuntu:24.04 AS base

USER root

COPY scripts/install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh

# Version of sage to build
ARG SAGEMATH_VERSION=

RUN  cd /usr/local \
  && git clone --depth 1 --branch ${SAGEMATH_VERSION} https://github.com/sagemath/sage.git

# Configure Sage
COPY scripts/configure-sage.sh /root
RUN chmod +x  /root/configure-sage.sh && ./root/configure-sage.sh && rm /root/configure-sage.sh

# Build Sage
COPY scripts/build-sage.sh /root
RUN chmod +x  /root/build-sage.sh && ./root/build-sage.sh && rm /root/build-sage.sh

# Some optional packages
COPY scripts/install-optional.sh /root
RUN chmod +x  /root/install-optional.sh && ./root/install-optional.sh && rm /root/install-optional.sh

# Add links
COPY scripts/links-to-sage.sh /root
RUN chmod +x  /root/links-to-sage.sh && ./root/links-to-sage.sh && rm /root/links-to-sage.sh


