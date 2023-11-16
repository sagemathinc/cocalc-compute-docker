ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update && apt-get install -qq -y python3-pip
ADD colab.sh env.txt /
RUN bash /colab.sh
RUN rm /colab.sh /env.txt

USER user
