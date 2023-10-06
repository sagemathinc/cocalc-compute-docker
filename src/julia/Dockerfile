ARG ARCH=

FROM sagemathinc/compute-python${ARCH} AS base

USER root

# Install Julia
# See https://julialang.org/downloads/ for current version

ARG JULIA=1.9.3

RUN cd /tmp \
 && export ARCH1=`uname -m | sed s/x86_64/x64/` \
 && export ARCH2=`uname -m` \
 && curl -s -O https://julialang-s3.julialang.org/bin/linux/${ARCH1}/${JULIA%.*}/julia-${JULIA}-linux-${ARCH2}.tar.gz \
 && tar xf julia-${JULIA}-linux-${ARCH2}.tar.gz -C /opt \
 && rm  -f julia-${JULIA}-linux-${ARCH2}.tar.gz \
 && mv /opt/julia-* /opt/julia \
 && ln -s /opt/julia/bin/julia /usr/local/bin

# Quick test that Julia actually works (i.e., we installed the right binary above).
RUN echo '2+3' | julia

# Install IJulia kernel
# I figured out the directory /opt/julia/local/share/julia by inspecting the global varaible
# DEPOT_PATH from within a running Julia session as a normal user, and also reading julia docs:
#    https://pkgdocs.julialang.org/v1/glossary/

RUN echo 'using Pkg; Pkg.add("IJulia");' | \
      JUPYTER=/usr/local/bin/jupyter \
      JULIA_DEPOT_PATH=/opt/julia/local/share/julia \
      JULIA_PKG=/opt/julia/local/share/julia \
      julia

RUN  mkdir -p /usr/local/share/jupyter/kernels/ \
  && mv "$HOME/.local/share/jupyter/kernels/julia"* "/usr/local/share/jupyter/kernels/"

# Also add the Pluto notebook server:
RUN echo 'using Pkg; Pkg.add("Pluto"); Pkg.add("Nemo"); Pkg.add("Hecke")' | \
      JULIA_DEPOT_PATH=/opt/julia/local/share/julia \
      JULIA_PKG=/opt/julia/local/share/julia \
      julia


WORKDIR /home/user
USER user
