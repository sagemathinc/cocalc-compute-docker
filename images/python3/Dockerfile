FROM sagemathinc/compute

RUN apt-get update \
    && apt-get install -y python3-pip \
    && pip install jupyter \
    && python3 -m ipykernel install

RUN apt-get clean && rm -rf /var/lib/apt/lists/*
