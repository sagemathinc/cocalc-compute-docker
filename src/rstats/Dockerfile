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

# Dependencies for installing the popular R packages
RUN \
  apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
     libharfbuzz-dev libfribidi-dev  libxml2-dev libssl-dev libgit2-dev

# Install R Jupyter Kernel package into R itself (so the R Jupyter kernel works),
# and some other packages e.g., rmarkdown which requires reticulate to use Python.
ADD install_packages.R /tmp

RUN Rscript --no-save /tmp/install_packages.R tidyverse
RUN Rscript --no-save /tmp/install_packages.R repr
RUN Rscript --no-save /tmp/install_packages.R IRdisplay IRkernel
RUN Rscript --no-save /tmp/install_packages.R evaluate
RUN Rscript --no-save /tmp/install_packages.R crayon
RUN Rscript --no-save /tmp/install_packages.R pbdZMQ
RUN Rscript --no-save /tmp/install_packages.R httr
RUN Rscript --no-save /tmp/install_packages.R devtools
RUN Rscript --no-save /tmp/install_packages.R uuid
RUN Rscript --no-save /tmp/install_packages.R digest
RUN Rscript --no-save /tmp/install_packages.R rmarkdown
RUN Rscript --no-save /tmp/install_packages.R reticulate
RUN Rscript --no-save /tmp/install_packages.R formatR
RUN Rscript --no-save /tmp/install_packages.R Cairo

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

# See https://forum.posit.co/t/missing-x11-support-in-rstudio/174814/2 and
# https://discourse.openondemand.org/t/graphics-display-issues-with-r-built-from-source-for-rstudio-server/1123/5
# File must end in a newline!!!!
#  https://github.com/easybuilders/easybuild-easyconfigs/issues/4918#issuecomment-417486880
COPY Rprofile.site /usr/local/lib/R/etc/Rprofile.site

# So user can easily install packages
RUN chown -R user:user /usr/local
RUN chown -R user:user /var/log

# RStudio shows a lot of errors without a proper locale setup.
RUN apt update && apt -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

COPY start-rstudio.sh /opt/start-rstudio.sh
RUN chmod a+x /opt/start-rstudio.sh
COPY rstudio.conf /etc/supervisor/conf.d/


WORKDIR /home/user
USER user
