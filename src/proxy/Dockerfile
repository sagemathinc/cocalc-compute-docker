FROM ubuntu:22.04
MAINTAINER William Stein <wstein@sagemath.com>

# Setup environment variables.
USER root

RUN apt update; apt install -y curl

# Install nodejs version 20.
RUN mkdir -p /nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | NVM_DIR=/nvm bash
RUN . /nvm/nvm.sh && nvm install --no-progress 20
RUN . /nvm/nvm.sh && npm install -g @cocalc/compute-server-proxy

# Copy over a simple default proxy that proxies port 80:
COPY proxy.json /proxy.json

# default token for testing:
RUN echo "test" > /token

# default env -- this can all get customized
ENV PROXY_CONFIG=/proxy.json
ENV PROXY_PORT=443
ENV PROXY_HOSTNAME=0.0.0.0
ENV PROXY_AUTH_TOKEN_FILE=/token
ENV DEBUG=*

CMD . /nvm/nvm.sh && npx @cocalc/compute-server-proxy