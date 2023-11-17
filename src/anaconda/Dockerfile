ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

ADD miniforge.sh environment.yml /
ADD conda-activate.sh /cocalc-compute-init.sh
RUN chmod a+x /cocalc-compute-init.sh
RUN bash /miniforge.sh
RUN rm /miniforge.sh /environment.yml

USER user
