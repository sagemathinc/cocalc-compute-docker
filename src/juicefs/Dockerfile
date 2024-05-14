ARG ARCH=
ARG BASE_TAG=
FROM sagemathinc/base${ARCH}:${BASE_TAG}

USER root

# RUN \
#      apt-get update \
#   && DEBIAN_FRONTEND=noninteractive apt-get install -y

ARG JFS_VERSION=
ARG ARCH1
RUN \
     cd /tmp/ \
  && mkdir juice \
  && curl -sSL "https://github.com/juicedata/juicefs/releases/download/v${JFS_VERSION}/juicefs-${JFS_VERSION}-linux-${ARCH1}.tar.gz" > a.tar.gz \
  && tar xvf a.tar.gz \
  && install juicefs /usr/local/bin \
  && rm -rf /tmp/juice

USER user


