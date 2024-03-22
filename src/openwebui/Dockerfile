ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

RUN apt-get update && apt-get install -y pciutils

COPY start-openwebui.sh /opt/start-openwebui.sh
RUN chmod a+x /opt/start-openwebui.sh

# Copy over the openwebui supervisord conf script.  Since
# the cocalc-compute npm package runs supervisord, it will
# pick this up and run it automatically.
COPY openwebui.conf /etc/supervisor/conf.d/openwebui.conf

USER user
