ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update \
    && apt-get install -y python3-pip \
    && pip install jupyter \
    && python3 -m ipykernel install

USER user
