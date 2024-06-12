The entire point of this image is to build the /cocalc directory
of code so that we can easily copy it into VM images, then mount
it into other containers. This isn't a Docker container that is
run, but is used as a store of files.

This builds just the part of cocalc that's needed for the compute
servers, so not the hubs of frontend or any of that.

---

Any scripts in /cocalc/bin are symlinked to /usr/local/bin in the compute container on startup (see start-compute.sh). So if you want to add a command that is available across all compute servers, that is the place to put it.
