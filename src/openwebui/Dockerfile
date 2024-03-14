ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

RUN apt-get update && apt-get install -y pciutils

# Proxy server configuration
COPY proxy.json /app/proxy.json
ENV PROXY_CONFIG=/app/proxy.json
ENV PROXY_PORT=443
ENV PROXY_HOSTNAME=0.0.0.0
ENV PROXY_AUTH_TOKEN_FILE=/cocalc/conf/auth_token

# Create a token just for testing.  In production use, this /cocalc will get bind mounted over.
RUN mkdir -p /cocalc/conf && echo "test" > /cocalc/conf/auth_token && chmod og-rwx /cocalc/conf/auth_token

# Install nodejs and our custom proxy server
RUN  mkdir -p /opt/proxy/nvm \
  && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | NVM_DIR=/opt/proxy/nvm bash \
  && source /opt/proxy/nvm/nvm.sh \
  && nvm install --no-progress 20

RUN source /opt/proxy/nvm/nvm.sh && npm install -g @cocalc/compute-server-proxy@latest
COPY start-proxy.sh /opt/proxy/start-proxy.sh

COPY start-openwebui.sh /opt/start-openwebui.sh
RUN chmod a+x /opt/start-openwebui.sh

RUN mkdir -p /var/log/supervisor && chown -R user:user /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

#

USER user
