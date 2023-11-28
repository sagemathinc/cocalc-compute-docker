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

COPY --from=ghcr.io/ollama-webui/ollama-webui:main /app /app

RUN apt-get update && apt-get install -y python3-pip

RUN cd /app/backend && pip3 install -r requirements.txt

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

USER user
