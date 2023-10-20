ARG ARCH=

FROM sagemathinc/compute-base${ARCH}

USER root
RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y unionfs-fuse

USER user
CMD /cocalc/start-filesystem.sh


