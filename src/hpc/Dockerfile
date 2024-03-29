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

# We also want the compilers etc to actually work without requiring users
# to fiddle with LD_LIBRARY_PATH.
# We dynamically set the INTEL_VERSION environment variable to the latest version
# by listing the directory and sorting, since we want this to work even when
# the date version changes.
RUN  INTEL_VERSION=$(ls /opt/intel/oneapi/compiler/ | grep ^2[0-9] | sort -V | tail -n 1) \
  && echo "/opt/intel/oneapi/compiler/$INTEL_VERSION/lib/" > /etc/ld.so.conf.d/intel-oneapi.conf \
  && ldconfig

# Test that intel fortran works by compiling and running a test program
#   https://people.math.sc.edu/Burkardt/f_src/f90/binary_tree.f90
RUN  mkdir /tmp/test-fortran
COPY binary_tree.f90 /tmp/test-fortran/binary_tree.f90
RUN cd /tmp/test-fortran && ifx binary_tree.f90 && ./a.out && rm a.out

# Install standard open source compilers (GNU and Clang)
RUN  apt-get update \
  && apt-get install -y gfortran dpkg-dev clang

RUN cd /tmp/test-fortran && gfortran binary_tree.f90 && ./a.out && rm a.out

# Install slurm job control support
RUN  apt-get update \
  && apt-get install -y slurmctld slurmd

RUN apt-get install -y supervisor

# Delete this secret key, which forces us to generate a new
# one the first time we start munge; critical to do this for
# security purposes, obviously!
RUN rm /etc/munge/munge.key

RUN rm -rf /tmp/test-fortran

COPY slurm.conf /etc/slurm/slurm.conf
COPY start-slurm.sh /etc/slurm/start-slurm.sh
COPY slurm-supervisor.conf /etc/supervisor/conf.d/slurm-supervisor.conf

USER user
