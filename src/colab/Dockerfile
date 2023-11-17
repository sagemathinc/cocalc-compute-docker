ARG ARCH=

FROM sagemathinc/compute${ARCH}
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

USER root

ADD colab.sh pip.txt apt.txt /
RUN bash /colab.sh
RUN rm /colab.sh /pip.txt /apt.txt

USER user
