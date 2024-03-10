# Activate default micromamba environment, set aliases,
# and print some instructions

export MAMBA_ROOT_PREFIX=/conda
eval "$(micromamba shell hook --shell bash)"
micromamba activate default
