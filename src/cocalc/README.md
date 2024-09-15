## How to update

If you edit code here and need to update and run it, see how to make the cocalc npm package, i.e., the top level README about stuff involving `make cocalc`.

## Background:

The entire point of this image is to build the /cocalc directory
of code so that we can easily copy it into VM images, then mount
it into other containers. This isn't a Docker container that is
run, but is used as a store of files.

In fact, that actual files are stored on npmjs.com, then installed
from there when the compute server starts; this turns out to be much
more efficient than using docker to grab some files.

This builds just the part of cocalc that's needed for the compute
servers, so not the hubs of frontend or any of that.

---

Any scripts in /cocalc/bin are symlinked to /usr/local/bin in the compute container on startup (see start-compute.sh). So if you want to add a command that is available across all compute servers, that is the place to put it.
