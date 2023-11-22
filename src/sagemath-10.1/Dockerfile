# When you change this, be sure to change Dockerfile-arm64 in the same way!!!

FROM sagemathinc/compute-python
USER user

COPY --from=sagemathinc/compute-sagemath-10.1-core /usr/local/sage /usr/local/sage

# run sage once. Otherwise, the first startup is very slow.
RUN /usr/local/sage/sage/sage < /dev/null

# Add links for sage and sagemath
USER root
RUN  ln -sf "/usr/local/sage/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage/sage" /usr/bin/sagemath

RUN apt-get update && apt-get install -y libssl-dev graphviz tachyon gfortran libreadline-dev

# Sage Jupyter kernel
RUN cp -r /usr/local/sage/sage/local/var/lib/sage/*/share/jupyter/kernels/sagemath  /usr/local/share/jupyter/kernels/

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
RUN sage --nodotsage -c "install_scripts('/usr/local/bin')"

WORKDIR /home/user

USER user
