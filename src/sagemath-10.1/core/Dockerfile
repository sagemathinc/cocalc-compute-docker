FROM ubuntu:22.04 AS base

USER root

COPY install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh

# Version of sage to build
ARG SAGE_VERSION=10.1

# Grab source code
RUN  cd /usr/local \
  && git clone --depth 1 --branch ${SAGE_VERSION} https://github.com/sagemath/sage.git

# Configure
RUN  export SAGE_FAT_BINARY="yes" \
  && export SAGE_INSTALL_GCC="no" \
  && cd /usr/local/sage \
  && make configure \
  && ./configure --enable-build-as-root

# Build
RUN  export SAGE_FAT_BINARY="yes" \
  && export SAGE_INSTALL_GCC="no" \
  && export MAKE="make -j`grep processor /proc/cpuinfo | wc -l`" \
  && cd /usr/local/sage/ \
  && make

# Optional packages: just sagetex for now
RUN  export SAGE_FAT_BINARY="yes" \
  && export SAGE_INSTALL_GCC="no" \
  && export MAKE="make -j`grep processor /proc/cpuinfo | wc -l`" \
  && cd /usr/local/sage/ \
  && ./sage -p sagetex

# Clean up artifacts from the sage build that we don't need for runtime
RUN cd /usr/local/sage \
  && make misc-clean \
  && rm -rf upstream/ src/doc/output/doctrees/

# Strip binaries -- this saves gigabytes of space and takes a while...
RUN cd /usr/local/sage \
  && LC_ALL=C find local/lib local/bin -type f -exec strip '{}' ';' 2>&1 | grep -v "File format not recognized" |  grep -v "File truncated" || true

# Save nearly 5GB -- only do after installing all sage stuff!:
RUN rm -rf /usr/local/sage/build/pkgs/sagelib/src/build

# And delete git repo stuff.
RUN rm -rf /usr/local/sage/.git

# Now use multisage build to squash all the images into one, so the
# result is much smaller (otherwise nothing
# we deleted above is really gone):
FROM ubuntu:22.04
USER root

COPY --from=base /usr/local/sage /usr/local/sage

# Add links for sage and sagemath
RUN  ln -sf "/usr/local/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage" /usr/bin/sagemath

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
RUN /usr/local/sage/sage --nodotsage -c "install_scripts('/usr/local/bin')"

# Install packages again, so users can build cython code, etc.
# Sage assumed these exist when it was built so they better be here.
COPY install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh


