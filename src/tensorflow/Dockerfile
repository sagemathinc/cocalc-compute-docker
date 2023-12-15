ARG TENSORFLOW_VERSION
FROM nvcr.io/nvidia/tensorflow:${TENSORFLOW_VERSION}

COPY pytorch/install-python-support.sh /tmp
RUN /tmp/install-python-support.sh && rm /tmp/install-python-support.sh

# Standard CoCalc compute setup:
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

USER user
CMD /cocalc/start-compute.sh
