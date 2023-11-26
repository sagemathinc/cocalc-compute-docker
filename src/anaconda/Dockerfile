FROM sagemathinc/compute

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

COPY bash.sh /tmp/
RUN cat /tmp/bash.sh >> /etc/bash.bashrc && rm /tmp/bash.sh

RUN mkdir /conda && chown user:user /conda
ENV MAMBA_ROOT_PREFIX=/conda

# Install micromamba self-contained binary
RUN \
     export BIN_FOLDER=/usr/local/bin \
  && export CONDA_FORGE_YES=yes \
  && "${SHELL}" <(curl -L micro.mamba.pm/install.sh) </dev/null

# Micromamba is a fast clean self contained "drop in replacement", so
# for the muscle memory of people just using this image quickly, let's
# make it easy on them.
RUN ln -s /usr/local/bin/micromamba /usr/local/bin/conda
RUN ln -s /usr/local/bin/micromamba /usr/local/bin/mamba

USER user

# Add some common channels and setup the default environment
RUN \
     micromamba config append channels conda-forge \
  && micromamba config append channels anaconda \
  && micromamba config append channels huggingface \
  && micromamba config append channels pytorch \
  && micromamba create --name default  python=3.11

# Install enough to run a Jupyter notebook, since
# some users would want to use conda through that.
COPY install.sh /tmp/
RUN /tmp/install.sh jupyter

RUN micromamba clean -a -y

