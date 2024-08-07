# It is VERY important that this docker container not get completely out of control in
# size.  I'm trying to keep it well below 500MB. The reason is because it is pulled the first
# time you mount a filesystem, and we don't want that to take too long (or use too much space).

ARG ARCH=
ARG BASE_TAG=
FROM sagemathinc/base${ARCH}:${BASE_TAG} AS base

USER root

# We do NOT need Docker for cloud-filesystem, but it was nice to use all the other things from sagemathinc/base
RUN apt-get remove -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


# Install gcsfuse from official repo following https://cloud.google.com/storage/docs/gcsfuse-install seems broken.
# We directly install from Github Releases instead.
ARG ARCH1=
ARG GCSFUSE_VERSION=
RUN \
     cd /tmp/ \
  && mkdir gcsfuse \
  && curl -sSL https://github.com/GoogleCloudPlatform/gcsfuse/releases/download/v${GCSFUSE_VERSION}/gcsfuse_${GCSFUSE_VERSION}_${ARCH1}.deb > a.deb \
  && dpkg -i a.deb \
  && rm /tmp/a.deb


# Build JuiceFS from source from our fork of JuiceFS.  Our patches adds a --client-id option, which
# is critical to prevent distributed filesystem corruption due to using async replication with keydb.
# Also critical is support for 64MB block size.  Do not exclude this or juicefs defaults to 16MB
# even if you set 64, and corruption will (probably) ensue.
COPY patches/juicefs /tmp/patches/juicefs
ARG JUICEFS_BRANCH=release-1.2
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive \
  && apt-get install -y build-essential golang \
  && git clone --branch ${JUICEFS_BRANCH} https://github.com/juicedata/juicefs /tmp/juicefs \
  && cd /tmp/juicefs \
  && git apply /tmp/patches/juicefs/* \
  && make -j4 \
  && cp juicefs /usr/local/bin \
  && rm -rf /tmp/juicefs \
  && rm -rf $HOME/go \
  && apt-get remove -y golang

# Install keydb.
# We build keydb from source, since (1) their official binaries assume systemd,
# and (2) I need to support use of min-slaves-to-write with multi-master replication,
# which I added in a patch.
COPY patches/keydb /tmp/patches/keydb
ARG KEYDB_BRANCH=RELEASE_6_3_4
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive \
  && apt-get install -y build-essential nasm autotools-dev autoconf libjemalloc-dev tcl tcl-dev uuid-dev libcurl4-openssl-dev libssl-dev \
  && git clone --depth 1 --branch ${KEYDB_BRANCH} --single-branch https://github.com/Snapchat/KeyDB.git /tmp/KeyDB \
  && cd /tmp/KeyDB \
  && git apply /tmp/patches/keydb/01-multimaster-min-slaves.patch \
  && make -j4 USE_SYSTEMD=no BUILD_TLS=no ENABLE_FLASH=no \
  && make install \
  && strip /usr/local/bin/keydb* \
  && rm -rf /tmp/KeyDB \
  && apt-get remove -y dpkg-dev build-essential nasm autotools-dev autoconf libjemalloc-dev tcl tcl-dev uuid-dev libcurl4-openssl-dev libssl-dev

# Python dependencies for scripts -- install via pip requires installing pip (300MB+), then remove it
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip \
  && pip install google-cloud-storage \
  && apt-get remove -y python3-pip

# Bup
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y bup python3-fuse

# More cleanup
RUN \
     apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/* /tmp/* /root/.cache

# Now use multisage build to squash all the images into one, so the
# result is much smaller (otherwise nothing we deleted above is really gone):
FROM ubuntu:24.04
USER root

COPY --from=base / /


# Directories for temporary files, caching, mounting, etc.
RUN \
     mkdir -p /var/cloud-filesystem /secrets /buckets \
  && chown user:user /var/cloud-filesystem /secrets /buckets \
  && chmod og-rwx /var/cloud-filesystem /secrets /buckets

COPY scripts/ /scripts/

USER user

# Quik sanity test that things aren't totally broken
RUN \
     juicefs version \
  && gcsfuse --version \
  && keydb-server --version

CMD /usr/bin/python3 -u /scripts/cloud_filesystem.py --cloud-filesystem-json=/cocalc/conf/cloud-filesystem.json