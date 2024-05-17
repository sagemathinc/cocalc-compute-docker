ARG ARCH=
ARG PYTHON_TAG=
FROM sagemathinc/python${ARCH}:${PYTHON_TAG}

# Install Julia

# The arm64 one looks like this:
#
# https://julialang-s3.julialang.org/bin/linux/aarch64/1.9/julia-1.9.4-linux-aarch64.tar.gz
#
# and the x86 one:
#
# https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-1.9.4-linux-x86_64.tar.gz

ARG JULIA_VERSION

USER root

# Make it so /opt is owned by user.  The julia symlink below is
# temporarily broken, but makes sense after the install below.
RUN mkdir -p /opt \
 && chown -R user:user /opt \
 && ln -s /opt/julia/bin/julia /usr/local/bin/julia \
 && mkdir -p /usr/local/share/jupyter/kernels/ \
 && chown -R user:user /usr/local/share/jupyter/kernels

# We do most of the rest of the install as the normal user, so they can easily install
# packages "system-wide" without having to use sudo.
USER user

RUN cd /tmp \
 && export ARCH1=`uname -m | sed s/x86_64/x64/` \
 && export ARCH2=`uname -m` \
 && curl -fsSL https://julialang-s3.julialang.org/bin/linux/${ARCH1}/${JULIA_VERSION%.*}/julia-${JULIA_VERSION}-linux-${ARCH2}.tar.gz > julia.tar.gz \
 && tar xf julia.tar.gz -C /opt \
 && rm  -f julia.tar.gz \
 && mv /opt/julia-* /opt/julia

# Quick test that Julia actually works (i.e., we installed the right binary above).
RUN echo '2+3' | julia

# Assign environment variables
# I figured out the directory /opt/julia/local/share/julia by inspecting the global variable
# DEPOT_PATH from within a running Julia session as a normal user, and also reading julia docs:
#    https://pkgdocs.julialang.org/v1/glossary/
# Doing this makes installing packages work "systemwide" rather than in ~/.local. We want
# them on the compute server image, not in the user's home dir.
ENV JULIA_DEPOT_PATH=/opt/julia/local/share/julia
ENV JULIA_PKG=/opt/julia/local/share/julia
ENV JUPYTER=/usr/local/bin/jupyter

# Install IJulia kernel
RUN echo 'using Pkg; Pkg.add("IJulia");' | julia

RUN mv -v "$HOME/.local/share/jupyter/kernels/julia"* "/usr/local/share/jupyter/kernels/"

# Add popular packages (see https://juliapackages.com/trending?sort=stars), to save user's some
# time getting going and for consistency with cocalc.
RUN echo 'using Pkg; Pkg.add("Pluto");' | julia
RUN echo 'using Pkg; Pkg.add("Plots");' | julia
RUN echo 'using Pkg; Pkg.add("Flux");' | julia
RUN echo 'using Pkg; Pkg.add("Makie");' | julia



WORKDIR /home/user
