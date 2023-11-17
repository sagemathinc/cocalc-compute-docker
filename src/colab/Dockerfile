ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update
RUN apt-get install -qq -y \
    lsb-release \
    python3-pip \
    python3-dev \
    pkg-config \
    build-essential
ADD colab.sh env.txt apt.txt /
RUN bash /colab.sh
RUN rm /colab.sh /env.txt /apt.txt

#USER user
