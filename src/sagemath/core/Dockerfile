FROM ubuntu:24.04 AS base

USER root

COPY scripts/install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh

# Version of sage to build
ARG SAGEMATH_VERSION=

RUN  cd /usr/local \
  && git clone --depth 1 --branch ${SAGEMATH_VERSION} https://github.com/sagemath/sage.git

# Configure Sage
COPY scripts/configure-sage.sh /root
RUN chmod +x  /root/configure-sage.sh && ./root/configure-sage.sh && rm /root/configure-sage.sh

# Build Sage
COPY scripts/build-sage.sh /root
RUN chmod +x  /root/build-sage.sh && ./root/build-sage.sh && rm /root/build-sage.sh

# Some optional packages
COPY scripts/install-optional.sh /root
RUN chmod +x  /root/install-optional.sh && ./root/install-optional.sh && rm /root/install-optional.sh

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
FROM ubuntu:24.04
USER root

COPY --from=base /usr/local/sage /usr/local/sage

# Install packages again, so users can build cython code, etc.
# Sage assumed these exist when it was built so they better be here.
COPY scripts/install-packages.sh /root
RUN chmod +x  /root/install-packages.sh && ./root/install-packages.sh && rm /root/install-packages.sh

# Add links
COPY scripts/links-to-sage.sh /root
RUN chmod +x  /root/links-to-sage.sh && ./root/links-to-sage.sh && rm /root/links-to-sage.sh


