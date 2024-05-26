FROM ubuntu:24.04
MAINTAINER William Stein <wstein@sagemath.com>
USER root

RUN \
     apt-get update \
  && DEBIAN_FRONTEND=noninteractive apt-get install -y wireguard python3 iproute2 iputils-ping \
  && apt-get clean \
  && rm -rf /var/cache/apt/lists

COPY conf.py /conf.py
COPY run.sh /run.sh

CMD /run.sh