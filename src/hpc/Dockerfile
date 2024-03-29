ARG ARCH=
FROM sagemathinc/python${ARCH}

USER root

ENV DEBIAN_FRONTEND=noninteractive

# Install Intel ifort (fortran) and all other Intel software kits, for AI, deep learning, etc.
# https://www.intel.com/content/www/us/en/docs/oneapi/installation-guide-linux/2023-1/apt.html
RUN  wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
     | gpg --dearmor > /usr/share/keyrings/oneapi-archive-keyring.gpg 2> /dev/null \
  && echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] https://apt.repos.intel.com/oneapi all main" \
     > /etc/apt/sources.list.d/oneAPI.list

RUN apt-get update && apt-get install -y intel-basekit
RUN apt-get update && apt-get install -y intel-hpckit

# The following aren't really for HPC and add 15GB.  They might be useful for another image later.
#RUN apt-get update && apt-get install -y intel-renderkit
#RUN apt-get update && apt-get install -y intel-aikit
#RUN apt-get update && apt-get install -y intel-iotkit
#RUN apt-get update && apt-get install -y intel-dlfdkit

# The above intel toolkits install everything in /opt and are all made available via this PATH:
#     /opt/intel/oneapi/2024.1/bin
# so we just symlink everything to /usr/local/bin:
RUN cd /usr/local/bin/ && ln -s /opt/intel/oneapi/*/bin/* .

# Install standard open source compilers (GNU and Clang)
RUN  apt-get update \
  && apt-get install -y gfortran dpkg-dev clang

# Install slurm job control support
RUN  apt-get update \
  && apt-get install -y slurmctld slurmd

RUN apt-get install -y supervisor

# Delete this secret key, which forces us to generate a new
# one the first time we start munge; critical to do this for
# security purposes, obviously!
RUN rm /etc/munge/munge.key

COPY slurm.conf /etc/slurm/slurm.conf
COPY start-slurm.sh /etc/slurm/start-slurm.sh
COPY slurm-supervisor.conf /etc/supervisor/conf.d/slurm-supervisor.conf

USER user
