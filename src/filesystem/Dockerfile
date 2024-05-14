ARG ARCH=
ARG BASE_TAG=
FROM sagemathinc/base${ARCH}:${BASE_TAG}

USER root

# unionfs-fuse -- used for our layered sync filesystem
# lz4 -- used for compression when transfering files for sync.
# file rsync  bsdextrautils (to provide hexdump) bzip2 (to provide bunzip2) unzip gunzip tar xz gzip -- used for filesystem operations by api/frontend, e.g., copying/moving/etc.
# yapf3 -- for formatting code
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y unionfs-fuse lz4 \
     rsync  bsdextrautils bzip2 unzip tar xz-utils \
     yapf3 file \
  && ln -s /usr/bin/yapf3 /usr/bin/yapf

USER user
CMD /cocalc/start-filesystem.sh


