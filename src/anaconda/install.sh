#!/usr/bin/env bash

set -ev

eval "$(micromamba shell hook --shell bash)"
micromamba activate default
micromamba install $*
