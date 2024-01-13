ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

COPY install-core-python.sh /tmp
RUN chmod a+x /tmp/install-core-python.sh && /tmp/install-core-python.sh && rm /tmp/install-core-python.sh

USER user
