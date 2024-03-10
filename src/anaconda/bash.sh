# Activate default micromamba environment, set aliases,
# and print some instructions

export MAMBA_ROOT_PREFIX=/conda
eval "$(micromamba shell hook --shell bash)"
micromamba activate default
if [ ! -f /home/user/.condarc ]; then
    # Add two default channels
    micromamba config append channels anaconda
    micromamba config append channels conda-forge
fi