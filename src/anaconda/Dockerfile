ARG ARCH=
FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

# Setup conda environment.  This ensures it is initialized both
#  (a) for the terminal, and -- because of /etc/bash.bashrc
#  (b) for the Jupyter kernel server -- because of /etc/cocalc/init.sh
COPY bash.sh /tmp/
RUN \
     mkdir -p /etc/cocalc/ \
  && cp /tmp/bash.sh /etc/cocalc/init.sh \
  && cat /tmp/bash.sh >> /etc/bash.bashrc \
  && rm /tmp/bash.sh \
  && chown user:user -R /etc/cocalc

RUN mkdir /conda && chown user:user /conda
# NOTE: this prefix is also hardcoded in bash.sh above!
ENV MAMBA_ROOT_PREFIX=/conda

# Install micromamba self-contained binary
RUN \
     export BIN_FOLDER=/usr/local/bin \
  && export CONDA_FORGE_YES=yes \
  && "${SHELL}" <(curl -L micro.mamba.pm/install.sh) </dev/null

# Micromamba is a very fast clean small self-contained "drop in replacement", so
# for the muscle memory of people just using this image quickly:
RUN ln -s /usr/local/bin/micromamba /usr/local/bin/conda
RUN ln -s /usr/local/bin/micromamba /usr/local/bin/mamba

USER user

# Add some common channels and setup the default environment
RUN \
     micromamba config append channels anaconda \
  && micromamba config append channels conda-forge \
  && micromamba create --name default  python=3.11

# Install enough to run a Jupyter notebook, since
# some users would want to use conda through that.
COPY install.sh /tmp/
RUN /tmp/install.sh jupyter

RUN micromamba clean -a -y

CMD source /etc/cocalc/init.sh && if [ -f /cocalc/start-compute.sh ]; then /cocalc/start-compute.sh; else bash; fi

