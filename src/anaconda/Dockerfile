ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y wget curl git vim

ADD miniforge.sh environment.yml /
ADD conda-activate.sh /conda-activate.sh
RUN chmod a+rx /conda-activate.sh
RUN bash /miniforge.sh
RUN rm /miniforge.sh /environment.yml

RUN echo "source /conda-activate.sh" >> /etc/bash.bashrc

USER user
