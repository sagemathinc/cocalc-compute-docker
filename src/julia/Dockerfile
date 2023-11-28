ARG ARCH=
FROM sagemathinc/python${ARCH} AS base

USER root

# Install Julia

# The arm64 one looks like this:
#
# https://julialang-s3.julialang.org/bin/linux/aarch64/1.9/julia-1.9.4-linux-aarch64.tar.gz
#
# and the x86 one:
#
# https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.4-linux-x86_64.tar.gz

ARG JULIA_VERSION

RUN cd /tmp \
 && export ARCH1=`uname -m | sed s/x86_64/x64/` \
 && export ARCH2=`uname -m` \
 && curl -fsSL https://julialang-s3.julialang.org/bin/linux/${ARCH1}/${JULIA_VERSION%.*}/julia-${JULIA_VERSION}-linux-${ARCH2}.tar.gz > julia.tar.gz \
 && tar xf julia.tar.gz -C /opt \
 && rm  -f julia.tar.gz \
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
