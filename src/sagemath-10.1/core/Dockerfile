ARG ARCH=

FROM ubuntu:22.04 AS base

USER root

RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y \
       software-properties-common \
       flex \
       bison \
       libreadline-dev \
       make \
       cmake \
       g++ \
       build-essential \
       gfortran \
       dpkg-dev \
       libssl-dev \
       graphviz \
       tachyon \
       python3-pip

RUN mkdir -p /usr/local/sage && chown -R user:user /usr/local/sage

USER user

# Version of sage to build
ARG SAGE_VERSION=10.1

# Grab source code
RUN  cd /usr/local/sage \
  && git clone --depth 1 --branch ${SAGE_VERSION} https://github.com/sagemath/sage.git

# Configure
RUN  export SAGE_FAT_BINARY="yes" \
  && export SAGE_INSTALL_GCC="no" \
  && cd /usr/local/sage/sage \
  && make configure \
  && ./configure

# Build
RUN  export SAGE_FAT_BINARY="yes" \
  && export SAGE_INSTALL_GCC="no" \
  && export MAKE="make -j`grep processor /proc/cpuinfo | wc -l`" \
  && cd /usr/local/sage/sage \
  && make

# Clean up artifacts from the sage build that we don't need for runtime
RUN cd /usr/local/sage/sage \
  && make misc-clean \
  && rm -rf upstream/ src/doc/output/doctrees/

# Strip binaries -- this saves gigabytes of space and takes a while...
RUN cd /usr/local/sage/sage \
  && LC_ALL=C find local/lib local/bin -type f -exec strip '{}' ';' 2>&1 | grep -v "File format not recognized" |  grep -v "File truncated" || true

# Save nearly 5GB -- only do after installing all sage stuff!:
RUN rm -rf /usr/local/sage/build/pkgs/sagelib/src/build

# And git repo stuff.
RUN rm -rf /usr/local/sage/.git

# Now squash all the images into one, so the result is much smaller (otherwise nothing
# we deleted above is really gone):
FROM ubuntu:22.04
USER root

COPY --from=base /usr/local/sage /usr/local/sage

# Add links for sage and sagemath
RUN  ln -sf "/usr/local/sage/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage/sage" /usr/bin/sagemath

RUN apt-get update && apt-get install -y libssl-dev graphviz tachyon gfortran libreadline-dev 

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
RUN sage --nodotsage -c "install_scripts('/usr/local/bin')"

