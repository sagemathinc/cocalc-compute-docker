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

# Install keydb.  I'm not worrying about exact versions yet, since this project rarely does releases.
# See https://docs.keydb.dev/docs/ppa-deb for package instructions.
# What we do below is WAY more complicated, since the official postinstall script assumes systemd,
# but in Docker there is no systemd.  So we recreate the keybd-server package with the
# postinst emptied.  This was suggested by GPT-4 and just works, so yeah!
# I also reported this upstream: https://github.com/Snapchat/KeyDB/issues/834
RUN \
     apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y lsb-release \
  && echo "deb https://download.keydb.dev/open-source-dist `lsb_release -sc` main" > /etc/apt/sources.list.d/keydb.list \
  && curl -sSL https://download.keydb.dev/open-source-dist/keyring.gpg > /etc/apt/trusted.gpg.d/keydb.gpg \
  && apt-get update \
  && mkdir /tmp/keydb \
  && cd /tmp/keydb \
  && apt-get download keydb-server keydb-tools keydb libsnappy1v5 \
  && dpkg-deb -R keydb-server_*.deb keydb-server \
  && echo "" > keydb-server/DEBIAN/postinst \
  && dpkg-deb -b keydb-server keydb-server_*.deb \
  && DEBIAN_FRONTEND=noninteractive dpkg -i *.deb \
  && rm -rf /tmp/keydb

USER user

# Quik sanity test that things aren't totally broken
RUN \
     juicefs version \
  && gcsfuse --version \
  && keydb-server --version


