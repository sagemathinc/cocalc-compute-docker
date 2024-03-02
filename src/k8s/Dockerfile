ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

# Install Kubernetes client binaries
COPY install-kubectl.sh /tmp
RUN chmod a+x /tmp/install-kubectl.sh && /tmp/install-kubectl.sh && rm /tmp/install-kubectl.sh

# Install Helm client binary
COPY install-helm.sh /tmp
RUN chmod a+x /tmp/install-helm.sh && /tmp/install-helm.sh && rm /tmp/install-helm.sh

USER user
