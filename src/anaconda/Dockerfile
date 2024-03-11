ARG ARCH=
FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

RUN mkdir /conda && chown user:user /conda

# Setup conda environment.  This ensures it is initialized both
#  (a) for the terminal, and -- because of /etc/bash.bashrc
#  (b) for the Jupyter kernel server -- because of /etc/cocalc/init.sh
COPY activate.sh /tmp/

RUN \
     cp /tmp/activate.sh /conda/activate.sh \
  && cat /tmp/activate.sh >> /etc/bash.bashrc \
  && rm /tmp/activate.sh \
  && chown user:user /conda/activate.sh

RUN ln -s /conda/bin/conda /usr/local/bin/conda && ln -s /conda/bin/mamba /usr/local/bin/mamba

USER user

# Install Mambaforge:
RUN \
      cd /tmp \
  && curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh \
  && sh Miniforge3-$(uname)-$(uname -m).sh -b -u -p /conda \
  && rm /tmp/Miniforge3-$(uname)-$(uname -m).sh


# Install enough to run a Jupyter notebook, since
# users would likely want to at least use conda
# through that.
RUN \
     eval "$(/conda/bin/conda shell.bash hook)" \
  && mamba create -n default \
  && mamba install -y jupyter \
  && mamba clean -a -y

CMD source /conda/activate.sh && if [ -f /cocalc/start-compute.sh ]; then /cocalc/start-compute.sh; else bash; fi
