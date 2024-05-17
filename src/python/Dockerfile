ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

# Install 'core python'
COPY install-core-python.sh /tmp
RUN chmod a+x /tmp/install-core-python.sh && /tmp/install-core-python.sh && rm /tmp/install-core-python.sh

# Make /usr/local be owned by user so that when they do "pip install" it
# installs packages and scripts systemwide. This keeps the installs on the
# compute server's local disk, avoiding conflict with other compute servers
# or use of the shared filesystem.
RUN chown -R user:user /usr/local

USER user
