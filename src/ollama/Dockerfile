ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

RUN apt-get update && apt-get install -y lshw

# Install ollama
#   https://github.com/jmorganca/ollama/releases/download/v0.1.12/ollama-linux-amd64
# and
#   https://github.com/jmorganca/ollama/releases/download/v0.1.12/ollama-linux-arm64
#
ARG ARCH1=
ARG OLLAMA_VERSION=

RUN curl -fSL -o /usr/local/bin/ollama https://github.com/jmorganca/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${ARCH1} \
  && chmod a+rx /usr/local/bin/ollama

# Install ollama-webui
# See https://github.com/ollama-webui/ollama-webui/pkgs/container/ollama-webui

ENV ENV=prod
ARG OLLAMA_API_BASE_URL='http://localhost:11434/api'
ENV OLLAMA_API_BASE_URL $OLLAMA_API_BASE_URL
ENV WEBUI_AUTH ""
ENV WEBUI_DB_URL ""
ENV WEBUI_JWT_SECRET_KEY "SECRET_KEY"

COPY --from=ghcr.io/ollama-webui/ollama-webui@sha256:b81ec9f68cceffba97158e77e266b3f278f96105687aad4d6731554c6a3444d6 /app /app

RUN apt-get update && apt-get install -y python3-pip

RUN cd /app/backend && pip3 install -r requirements.txt

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

ARG PROXY_VERSION=latest
RUN source /opt/proxy/nvm/nvm.sh && npm install -g @cocalc/compute-server-proxy@${PROXY_VERSION}
COPY start-proxy.sh /opt/proxy/start-proxy.sh

RUN mkdir -p /var/log/supervisor && chown -R user:user /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

USER user
