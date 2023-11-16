ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y wget

ADD miniforge.sh environment.yml /
ADD conda-activate.sh /bin/conda-activate.sh
RUN chmod a+x /bin/conda-activate.sh
RUN bash /miniforge.sh
RUN rm /miniforge.sh /environment.yml

USER user
