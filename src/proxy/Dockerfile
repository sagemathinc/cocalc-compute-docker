FROM ubuntu:22.04
MAINTAINER William Stein <wstein@sagemath.com>

# Setup environment variables.
USER root

RUN apt update; apt install -y curl

# Install nodejs version 20.
RUN mkdir -p /nvm
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | NVM_DIR=/nvm bash
RUN . /nvm/nvm.sh && nvm install --no-progress 20
RUN . /nvm/nvm.sh && npm install -g pnpm

# Copy source code for our proxy server over.
COPY src /proxy
# Copy over a simple default proxy configuration that proxies port 80:
COPY proxy.json /proxy/proxy.json
RUN cd /proxy && . /nvm/nvm.sh && pnpm install
RUN cd /proxy && . /nvm/nvm.sh && pnpm build
RUN cd /proxy && . /nvm/nvm.sh && pnpm audit

# default token for testing:
RUN echo "test" > /token

# default env -- this can all get customized
ENV PROXY_CONFIG=/proxy/proxy.json
ENV PROXY_PORT=443
ENV PROXY_HOSTNAME=0.0.0.0
ENV PROXY_AUTH_TOKEN_FILE=/token
ENV DEBUG=*

CMD . /nvm/nvm.sh && cd /proxy && ./bin/start-proxy.js

# For testing, it is useful to exec into the container and install and run vscode:
#  make run-proxy
#  docker exec -it run-proxy bash
#    curl -fsSL https://code-server.dev/install.sh | sh && code-server --bind-addr=localhost:80 --auth=none
# and
#    apt install -y python-is-python3 && python3 -m http.server 9000
# and
#    apt update; apt install -y python3-pip; pip3 install jupyterlab; jupyter lab --NotebookApp.token='' --NotebookApp.password='' --ServerApp.disable_check_xsrf=True --no-browser --NotebookApp.allow_remote_access=True --NotebookApp.base_url='/port/8888' --ip=localhost --port=8888 --allow-root