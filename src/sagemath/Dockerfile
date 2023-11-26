FROM sagemathinc/python

# Install packages that Sage assumes are there
USER root
COPY core/install-packages.sh /tmp/install-packages.sh
RUN chmod +x /tmp/install-packages.sh && /tmp/install-packages.sh

USER user

ARG SAGEMATH_VERSION
COPY --from=sagemathinc/sagemath-core:$SAGEMATH_VERSION /usr/local/sage /usr/local/sage

# Run sage once; otherwise, the first startup is slow.
RUN /usr/local/sage/sage < /dev/null

# Add links for sage and sagemath
USER root
RUN  ln -sf "/usr/local/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage" /usr/bin/sagemath

# Sage Jupyter kernel
RUN cp -r /usr/local/sage/local/var/lib/sage/*/share/jupyter/kernels/sagemath  /usr/local/share/jupyter/kernels/

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
RUN sage --nodotsage -c "install_scripts('/usr/local/bin')"

WORKDIR /home/user

USER user
