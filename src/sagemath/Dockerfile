ARG PYTHON_TAG=
ARG SAGEMATH_VERSION=
ARG ARCH=
ARG SAGEMATH_VARIANT=
FROM sagemathinc/sagemath-${SAGEMATH_VARIANT}${ARCH}:${SAGEMATH_VERSION} as sagemath
FROM sagemathinc/python${ARCH}:${PYTHON_TAG}

# Install packages that Sage assumes are there
USER root
COPY scripts/install-packages.sh /tmp/install-packages.sh
RUN chmod +x /tmp/install-packages.sh && /tmp/install-packages.sh

USER user

COPY --from=sagemath /usr/local/sage /usr/local/sage

# Run sage once; otherwise, the first startup is slow.
RUN /usr/local/sage/sage < /dev/null

# Add links for sage and sagemath
USER root
RUN  ln -sf "/usr/local/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage" /usr/bin/sagemath

# Sage Jupyter kernel
RUN cp -r /usr/local/sage/local/var/lib/sage/*/share/jupyter/kernels/sagemath  /usr/local/share/jupyter/kernels/

# Add links
COPY scripts/links-to-sage.sh /root
COPY scripts/install_scripts.py /root
RUN chmod +x  /root/links-to-sage.sh && cd /root && ./links-to-sage.sh && rm links-to-sage.sh install_scripts.py

WORKDIR /home/user

USER user


# Note there is a trick used above for copying from a specific tag of another image. See
# https://forums.docker.com/t/how-can-i-expand-a-variable-within-a-copy-command-in-the-dockerfile/113538/7
