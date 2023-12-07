ARG CUDA_VERSION=
FROM nvcr.io/nvidia/cuda:${CUDA_VERSION}

MAINTAINER William Stein <wstein@sagemath.com>

# Standard CoCalc compute setup
ENV LC_ALL=C.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV TERM=screen
ENV DEBUG_CONSOLE=yes
ENV PIP_ROOT_USER_ACTION=ignore

USER root
COPY base/install-core-packages.sh /tmp/install-core-packages.sh
RUN /tmp/install-core-packages.sh
COPY base/install-docker.sh /tmp/install-docker.sh
RUN /tmp/install-docker.sh
COPY base/setup-user.sh /tmp/setup-user.sh
RUN /tmp/setup-user.sh
COPY base/scripts/* /usr/local/bin/

# The cuda compiler tools are installed into /usr/local/cuda/bin,
# so we add them to the PATH.
RUN echo 'export PATH=/usr/local/cuda/bin:$PATH' >> /etc/bash.bashrc

USER user
ENTRYPOINT []
CMD /cocalc/start-compute.sh
