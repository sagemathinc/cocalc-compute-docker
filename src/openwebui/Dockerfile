ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

RUN apt-get update && apt-get install -y pciutils

# Create a token just for testing.  In production use, this /cocalc will get bind mounted over this
RUN mkdir -p /cocalc/conf && echo "test" > /cocalc/conf/auth_token && chmod og-rwx /cocalc/conf/auth_token
# Similar for proxy.json for testing:
COPY .proxy.json /cocalc/conf/proxy.json

COPY start-openwebui.sh /opt/start-openwebui.sh
RUN chmod a+x /opt/start-openwebui.sh

# Copy over the openwebui supervisord conf script.  Since
# the cocalc-compute npm package runs supervisord, it will
# pick this up and run it automatically.
COPY openwebui.conf /etc/supervisor/conf.d/openwebui.conf

USER user
