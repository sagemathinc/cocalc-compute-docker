ARG ARCH=

FROM sagemathinc/compute-python${ARCH}
USER user

COPY --from=sagemathinc/compute-sagemath-10.1-core /usr/local/sage /usr/local/sage

# run sage once. Otherwise, the first startup is very slow. 
RUN /usr/local/sage/sage/sage < /dev/null

# Add links for sage and sagemath
USER root
RUN  ln -sf "/usr/local/sage/sage/sage" /usr/bin/sage \
  && ln -sf "/usr/local/sage/sage/sage" /usr/bin/sagemath

RUN apt-get update && apt-get install -y libssl-dev graphviz tachyon gfortran libreadline-dev 

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
RUN sage --nodotsage -c "install_scripts('/usr/local/bin')"

WORKDIR /home/user

USER user
