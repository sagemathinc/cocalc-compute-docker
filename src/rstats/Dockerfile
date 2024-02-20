ARG ARCH=
FROM sagemathinc/python${ARCH} AS base

USER root

# Install the R statistical software.  We do NOT use a custom repo, etc., as
# suggested https://github.com/sagemathinc/cocalc-docker/pull/169/files because
# it doesn't work on our supported platforms (e.g., arm64).  If you need
# the latest R, please install it yourself.
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
     build-essential r-base \
     libopenblas-dev liblapack-dev libx11-dev libxt-dev libcurl4-openssl-dev \
     libpng-dev libjpeg-dev libtiff-dev libcairo2-dev

ARG R_VERSION
COPY build-r.sh /tmp
RUN /tmp/build-r.sh ${R_VERSION}

# Did it work?
RUN /usr/local/bin/R --version

# Install R Jupyter Kernel package into R itself (so the R Jupyter kernel works),
# and some other packages e.g., rmarkdown which requires reticulate to use Python.
RUN echo "options(Ncpus = 8); install.packages(c('tidyverse', 'repr', 'IRdisplay', 'evaluate', 'crayon', 'pbdZMQ', 'httr', 'devtools', 'uuid', 'digest', 'IRkernel', 'rmarkdown', 'reticulate', 'formatR', 'Cairo'), repos='https://cloud.r-project.org')" | R --no-save

COPY ir /usr/local/share/jupyter/kernels/ir

RUN chmod a+r -R /usr/local/share/jupyter/kernels

# Install R Studio Server
# See https://dailies.rstudio.com/
#  and then https://dailies.rstudio.com/rstudio/chocolate-cosmos/server/jammy-amd64/
#           https://dailies.rstudio.com/rstudio/chocolate-cosmos/server/jammy-arm64/
# I could not find stable rstudio builds for ARM64.
ARG ARCH1=
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y gdebi-core libssl-dev libclang-dev psmisc \
  && wget https://s3.amazonaws.com/rstudio-ide-build/server/jammy/${ARCH1}/rstudio-server-2024.04.0-daily-470-${ARCH1}.deb \
  && echo "y" | dpkg -i rstudio-server-2024.04.0-daily-470-${ARCH1}.deb

# RStudio shows a lot of errors without a proper locale setup.
RUN apt update && apt -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Proxy server configuration
COPY proxy.json /app/proxy.json
ENV PROXY_CONFIG=/app/proxy.json
ENV PROXY_PORT=443
ENV PROXY_HOSTNAME=0.0.0.0
ENV PROXY_AUTH_TOKEN_FILE=/cocalc/conf/auth_token

# Create a token for testing.  In production use, this /cocalc will get bind mounted over.
RUN mkdir -p /cocalc/conf && echo "test" > /cocalc/conf/auth_token && chmod og-rwx /cocalc/conf/auth_token

# Install nodejs and our custom proxy server
RUN  mkdir -p /opt/proxy/nvm \
  && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | NVM_DIR=/opt/proxy/nvm bash \
  && source /opt/proxy/nvm/nvm.sh \
  && nvm install --no-progress 20

RUN apt install -y supervisor

ARG PROXY_VERSION=latest
RUN source /opt/proxy/nvm/nvm.sh && npm install -g @cocalc/compute-server-proxy@${PROXY_VERSION}
COPY start-proxy.sh /opt/proxy/start-proxy.sh
COPY start-rstudio.sh /opt/start-rstudio.sh
RUN chmod a+x /opt/start-rstudio.sh

RUN mkdir -p /var/log/supervisor && chown -R user:user /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

WORKDIR /home/user
USER user
