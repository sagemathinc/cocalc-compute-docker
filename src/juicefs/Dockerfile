ARG ARCH=
ARG BASE_TAG=
FROM sagemathinc/base${ARCH}:${BASE_TAG}

USER root

# Install JuiceFS Go binary -- https://juicefs.com/docs/community/getting-started/installation/
# We do things more manually so we explicitly update version instead of it randomly
# updating whenever we build the image.
ARG JFS_VERSION=
ARG ARCH1
RUN \
     cd /tmp/ \
  && mkdir juice \
  && curl -sSL "https://github.com/juicedata/juicefs/releases/download/v${JFS_VERSION}/juicefs-${JFS_VERSION}-linux-${ARCH1}.tar.gz" > a.tar.gz \
  && tar xvf a.tar.gz \
  && install juicefs /usr/local/bin \
  && rm -rf /tmp/juice

# Install gcsfuse from official repo following https://cloud.google.com/storage/docs/gcsfuse-install seems broken.
# We directly install from Github Releases instead.
ARG GCSFUSE_VERSION=
RUN \
     cd /tmp/ \
  && mkdir gcsfuse \
  && curl -sSL https://github.com/GoogleCloudPlatform/gcsfuse/releases/download/v${GCSFUSE_VERSION}/gcsfuse_${GCSFUSE_VERSION}_${ARCH1}.deb > a.deb \
  && dpkg -i a.deb

USER user

# this is just a sanity test that things aren't totally broken
RUN \
     juicefs version \
  && gcsfuse --version


