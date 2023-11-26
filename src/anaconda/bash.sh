# Activate default micromamba environment, set aliases,
# and print some instructions

eval "$(micromamba shell hook --shell bash)"
micromamba activate default
echo "---------------------------------------------------------------"
echo "| Welcome to the CoCalc Anaconda Image                        |"
echo "| Type 'conda -h' for how to search for and install packages. |"
echo "---------------------------------------------------------------"
