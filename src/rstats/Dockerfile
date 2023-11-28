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

WORKDIR /home/user
USER user
