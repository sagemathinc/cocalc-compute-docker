ARG BASE_TAG=
ARG ARCH=
FROM sagemathinc/base${ARCH}:${BASE_TAG}

USER root

# Copy over the cocalc scripts -- this is to make testing and devel easier.
# In production these are mounted in.
COPY cocalc /cocalc

USER user

CMD /cocalc/start-compute.sh

