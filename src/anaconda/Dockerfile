FROM sagemathinc/compute

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

RUN mkdir /mamba && chown user:user /mamba
ENV MAMBA_ROOT_PREFIX=/mamba

# Install micromamba self-contained binary
RUN \
     export BIN_FOLDER=/usr/local/bin \
  && export CONDA_FORGE_YES=yes \
  && "${SHELL}" <(curl -L micro.mamba.pm/install.sh) </dev/null

RUN echo 'eval "$(micromamba shell hook --shell bash)"' >> /etc/bash.bashrc
# Activate our default environment, by default
RUN echo "micromamba activate default" >> /etc/bash.bashrc
# Micromamba is a fast clean self contained "drop in replacement", so
# for the muscle memory of people just using this image quickly, let's
# make it easy on them.
RUN echo "alias conda=micromamba" >>  /etc/bash.bashrc
RUN echo "alias mamba=micromamba" >>  /etc/bash.bashrc

USER user

RUN \
     micromamba config append channels conda-forge \
  && micromamba config append channels anaconda \
  && micromamba config append channels huggingface \
  && micromamba config append channels pytorch \
  && micromamba config append channels defaults \
  && micromamba create --name default python=3.11

USER root
RUN echo 'echo "-----------------------------------------------------------------------------------"' >>  /etc/bash.bashrc
RUN echo 'echo "This is a Micromamba Anaconda Python environment."' >>  /etc/bash.bashrc
RUN echo 'echo "Use conda list to see all packages and conda install to install new ones."' >>  /etc/bash.bashrc
RUN echo 'echo "-----------------------------------------------------------------------------------"' >>  /etc/bash.bashrc
USER user