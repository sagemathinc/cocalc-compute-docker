ARG ARCH=

FROM sagemathinc/compute${ARCH}

USER root

RUN apt-get update \
    && apt-get install -y python3-pip \
    && pip install jupyter \
    && python3 -m ipykernel install

# Popular python libraries
RUN pip install matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx

USER user
