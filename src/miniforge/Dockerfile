ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

ADD miniforge.sh /miniforge.sh
ADD environment.yml /environment.yml
RUN bash /miniforge.sh
RUN rm /miniforge.sh /environment.yml

USER user
