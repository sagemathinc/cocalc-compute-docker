FROM sagemathinc/compute

USER root

RUN apt-get update \
    && apt-get install -y lshw

# Install ollama
#   https://github.com/jmorganca/ollama/releases/download/v0.1.12/ollama-linux-amd64
# and
#   https://github.com/jmorganca/ollama/releases/download/v0.1.12/ollama-linux-arm64
#
ARG ARCH1=
ARG OLLAMA_VERSION=

RUN curl -fSL -o /usr/local/bin/ollama https://github.com/jmorganca/ollama/releases/download/v${OLLAMA_VERSION}/ollama-linux-${ARCH1} \
  && chmod a+rx /usr/local/bin/ollama

USER user
