set -v

git clone https://github.com/sagemath/sage
cd sage
make
./configure
export MAKE="make -j8"
time make build
