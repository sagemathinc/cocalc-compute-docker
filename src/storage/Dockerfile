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
  && rm -rfv /tmp/juicefs /tmp/a.tar.gz

# Install gcsfuse from official repo following https://cloud.google.com/storage/docs/gcsfuse-install seems broken.
# We directly install from Github Releases instead.
ARG GCSFUSE_VERSION=
RUN \
     cd /tmp/ \
  && mkdir gcsfuse \
  && curl -sSL https://github.com/GoogleCloudPlatform/gcsfuse/releases/download/v${GCSFUSE_VERSION}/gcsfuse_${GCSFUSE_VERSION}_${ARCH1}.deb > a.deb \
  && dpkg -i a.deb \
  && rm /tmp/a.deb

# Install keydb.
ARG KEYDB_VERSION=
# We build keydb from source, since their official binaries assume systemd.
# I also reported this upstream: https://github.com/Snapchat/KeyDB/issues/834
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive \
  && apt-get install -y build-essential nasm autotools-dev autoconf libjemalloc-dev tcl tcl-dev uuid-dev libcurl4-openssl-dev libssl-dev \
  && git clone --branch v${KEYDB_VERSION} --depth 1 https://github.com/Snapchat/KeyDB.git /tmp/KeyDB \
  && cd /tmp/KeyDB \
  && git submodule init && git submodule update \
  && make -j4 USE_SYSTEMD=no BUILD_TLS=no ENABLE_FLASH=no \
  && make install \
  && strip /usr/local/bin/keydb* \
  && rm -rf /tmp/KeyDB \
  && apt-get remove -y build-essential nasm autotools-dev autoconf libjemalloc-dev tcl tcl-dev uuid-dev libcurl4-openssl-dev libssl-dev \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/* /tmp/*

# Directories for temporary files, caching, mounting, etc.
RUN \
     mkdir /storage /secrets /buckets
  && chown user:user /storage /secrets /buckets \
  && chmod og-rwx /storage /secrets /buckets

COPY scripts/ /scripts/

USER user

# Quik sanity test that things aren't totally broken
RUN \
     juicefs version \
  && gcsfuse --version \
  && keydb-server --version

CMD /scripts/storage.py --storage-json=/cocalc/conf/storage.json