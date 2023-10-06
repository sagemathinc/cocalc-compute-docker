ARG ARCH=

FROM sagemathinc/compute-python${ARCH} AS base

USER root

# Install the R statistical software.  We do NOT use a custom repo, etc., as
# suggested https://github.com/sagemathinc/cocalc-docker/pull/169/files because
# it doesn't work on our supported platforms (e.g., arm64).  If you need
# the latest R, please install it yourself.
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y r-base r-cran-tidyverse tidy

# Install R Jupyter Kernel package into R itself (so the R Jupyter kernel works), 
# and some other packages e.g., rmarkdown which requires reticulate to use Python.
RUN echo "install.packages(c('repr', 'IRdisplay', 'evaluate', 'crayon', 'pbdZMQ', 'httr', 'devtools', 'uuid', 'digest', 'IRkernel', 'rmarkdown', 'reticulate', 'formatR'), repos='https://cloud.r-project.org')" | R --no-save

WORKDIR /home/user
USER user
