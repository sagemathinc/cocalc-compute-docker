#!/usr/bin/env Rscript

# see https://stackoverflow.com/questions/26244530/how-do-i-make-install-packages-return-an-error-if-an-r-package-cannot-be-install

options(Ncpus = 8)

packages = commandArgs(trailingOnly=TRUE)

for (l in packages) {

    install.packages(l, dependencies=TRUE, repos='https://cloud.r-project.org');

    if ( ! library(l, character.only=TRUE, logical.return=TRUE) ) {
        quit(status=1, save='no')
    }
}