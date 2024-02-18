ARG COMPUTE_TAG=
ARG ARCH=
FROM sagemathinc/compute${ARCH}:${COMPUTE_TAG}

USER root

# Install 'core python', which is the default ubuntu 22.04 rock solid python-3.10.
COPY install-core-python.sh /tmp
RUN chmod a+x /tmp/install-core-python.sh && /tmp/install-core-python.sh && rm /tmp/install-core-python.sh

# # Also install python3.11
# We do not do this yet, since it fails on ARM64 with not being able to install psutils, which is a
# dependency of Jupyter.  So really python 3.11 is just not properly supported yet.
# ENV DEBIAN_FRONTEND=noninteractive
# RUN apt-get install -y software-properties-common
# RUN add-apt-repository -y ppa:deadsnakes/ppa
# RUN apt install -y python3.11 python3.11-dev
# RUN python3.11 -m pip install matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx
# # Install the Jupyter kernels for core python 3.10 and also for 3.11.
# RUN python3.11 -m pip install jupyter \
#  && python3.11 -m ipykernel install --name python3.11 --display-name "Python `python3.11 --version | awk '{print $2}'`"

# Make /usr/local be owned by user so that when they do "pip install" it
# installs packages and scripts systemwide. This keeps the installs on the
# compute server's local disk, avoiding conflict with other compute servers
# or use of the shared filesystem.
RUN chown -R user:user /usr/local

USER user
