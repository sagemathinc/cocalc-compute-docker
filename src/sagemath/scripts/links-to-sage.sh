#!/usr/bin/env bash

set -ev

ln -sf "/usr/local/sage/sage" /usr/bin/sage
ln -sf "/usr/local/sage/sage" /usr/bin/sagemath

# Put scripts to start gap, gp, maxima, ... in /usr/local/bin
/usr/local/sage/sage -c "import sys; sys.path.append('.'); from install_scripts import install_scripts; install_scripts('/usr/local/bin')"
