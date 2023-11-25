FROM sagemathinc/base

USER root

# unionfs-fuse -- used for our layed sync filesystem
# lz4 -- used for compression when transfering files for sync.
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y unionfs-fuse lz4

USER user
CMD /cocalc/start-filesystem.sh


