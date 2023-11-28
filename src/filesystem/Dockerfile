ARG BASE_TAG=
FROM sagemathinc/base:${BASE_TAG}

USER root

# Copy over the cocalc script -- this is to make testing and devel easier.
# In production these are mounted in.
COPY cocalc /cocalc

# unionfs-fuse -- used for our layed sync filesystem
# lz4 -- used for compression when transfering files for sync.
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y unionfs-fuse lz4

USER user
CMD /cocalc/start-filesystem.sh


