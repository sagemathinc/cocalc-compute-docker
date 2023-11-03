# This doesn't work!
# E.g., I tried https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 starting
# with the tensorflow model, and it just doesn't work:
#   https://github.com/microsoft/TaskMatrix/issues/116#issuecomment-1782609748
# I think the right approach is just enhancing the tensorflow and pytorch
# images separately, rather than trying to have one massive env?

FROM sagemathinc/compute-tensorflow

RUN pip install \
    transformers diffusers invisible_watermark accelerate safetensors \
    pytorch torchvision torchtext torchaudio

USER user

CMD /cocalc/start-compute.sh

