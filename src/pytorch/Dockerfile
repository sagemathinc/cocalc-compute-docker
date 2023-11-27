# See https://catalog.ngc.nvidia.com/orgs/nvidia/containers/pytorch
FROM nvcr.io/nvidia/pytorch:23.10-py3

# To easily install certain things from Hugging Face, we install
# libraries that huggingface libraries use.
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6
RUN pip install diffusers transformers diffusers invisible_watermark accelerate safetensors sentencepiece

# Also, some popular python libraries
RUN pip install matplotlib pandas numpy scipy scikit-learn requests beautifulsoup4 sympy mpmath pyyaml networkx

# Standard CoCalc compute setup:
ENV LC_ALL=C.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV TERM=screen
ENV DEBUG_CONSOLE=yes
ENV PIP_ROOT_USER_ACTION=ignore

USER root
COPY base/install-core-packages.sh /tmp/install-core-packages.sh
RUN /tmp/install-core-packages.sh
COPY base/install-docker.sh /tmp/install-docker.sh
RUN /tmp/install-docker.sh
COPY base/setup-user.sh /tmp/setup-user.sh
RUN /tmp/setup-user.sh
COPY base/scripts/* /usr/local/bin/

USER user
CMD /cocalc/start-compute.sh
