# CoCalc Compute Server Image Management Repo

URL: https://github.com/sagemathinc/cocalc-compute-docker

[Compute Server Documentation](https://doc.cocalc.com/compute_server.html)

There will be sections below with step-by-step instructions
about how to update, build and test the compute server Docker images and npm pacckages we manage. For things that aren't documented yet, you have to
just read the source code, Makefiles and Dockerfiles. The Makefile is useful as a makefile, but it's not at all a traditional "bullet proof" makefile that ensure any relevant dependency is automatically built. It's a useful way to run scripts, as documented here, and that is all.

## Architectures: `x86_64` and `arm64`

I've taken great pains to ensure we fully support both architectures. This adds complexity and extra work at every step, unfortunately.

## How to update the cocalc npm package

To build the cocalc npm package and push it to npmjs with the label "test":

1. Update version of cocalc in this line in [images.json](./images.json): `{ "label": "test", "version": "1.8.1", "tag": "test", "tested": false }`
   e.g., from 1.8.1 to something newer than any tag, e.g., 1.8.3 or 1.9.0. 
```sh
make cocalc && make push-cocalc
```
2. Create a compute sever on [cocalc.com](http://cocalc.com) and for the images check "Advanced" and then select the "test" version of cocalc. That compute server will then use this testing npm package.

When ready to release in prod, i.e., to push a package to npmjs with the label "latest":

1. Update this line in images.json `{ "label": "latest", "version": "1.8.2", "tag": "latest", "tested": true }`,
   e.g., from 1.8.2 to 1.8.4, which is newer than the one you just tested
2. Then

```sh
make COCALC_TAG=latest cocalc && make COCALC_TAG=latest push-cocalc
```

You should also commit and push to github the new images.json file, though that isn't strictly necessary \(since the compute server uses the latest and test tags, not the npm package version\).

NOTE: You should do the above on both `x86_64` and `arm64` architectures, as they are separate. There is code in the cocalc package that is platform specific.

Double check versions at

- https://www.npmjs.com/package/@cocalc/compute-server?activeTab=versions

and at

- https://www.npmjs.com/package/@cocalc/compute-server-arm64?activeTab=versions

## How to update Julia

Add a new entry to the versions section of images.json for julia, e.g.,
I just added the 1.10.1 tag below, since as I write this Julia 1.10.1 was just released:

```json
  "julia": {
    ...
    "versions": [
      { "label": "1.9.4", "tag": "1.9.4", "tested": true },
      { "label": "1.10.0", "tag": "1.10.0", "tested": true },
      { "label": "1.10.1", "tag": "1.10.1", "tested": false },
    ],
```

Here the label is what the user sees in the dropdown list, and the tag is what we use internally everywhere. Typically they are the same, but they don't have to be.  You can also specify `"version":"1.10.1", "tag":"1.10.1.p1"` if you want to build Julia version 1.10.1, but use the tag `1.10.1.p1`.

Build the Julia Docker image, which should take 10-15 minutes.

```sh
make julia
```

Run it and test whatever you want in the shell:

```sh
make run-julia
```

E.g., you can confirm installed packages:

```sh
julia> using Pkg; Pkg.status()
Status `/opt/julia/local/share/julia/environments/v1.10/Project.toml`
  [587475ba] Flux v0.14.11
  [7073ff75] IJulia v1.24.2
  [ee78f7c6] Makie v0.20.7
  [91a5bcdd] Plots v1.40.1
  [c3e4b0f8] Pluto v0.19.38
```

Or run the Jupyter kernel

```sh
user@1e38d84d26cb:~$ jupyter kernelspec list
Available kernels:
  julia-1.10    /usr/local/share/jupyter/kernels/julia-1.10
  python3       /usr/local/share/jupyter/kernels/python3
user@1e38d84d26cb:~$ jupyter console --kernel=julia-1.10
```

Push it to DockerHub. This is not "dangerous", since no cocalc install
will use it until the images.json is pushed and explicitly lists this
version as existing and being tested:

```sh
make push-julia
```

Once you also do all this with ARM64 version, you can then assemble the x86_64 and arm64 Julia images into a single multiplatform Docker image:

```
make assemble-julia
```

In images.json, set this version as tested:

```json
  "julia": {
    ...
    "versions": [
      { "tag": "1.9.4", "tested": true },
      { "tag": "1.10.0", "tested": true },
      { "tag": "1.10.1", "tested": true },
    ],
```

You can now commit and push images.json.  
What this does is make it so on-prem compute server users get
this new version of the Julia image. Google cloud users still get
the latest version that was built and tested as a premade image there.

### Building a new Google Cloud Julia image

After updating `image.json` and pushing it so it is public, to build a
Google cloud image you have to explicitly get a shell on say hub-mentions in
the test namespace.
From there you can run code to build a new Google cloud image as explained in the comment at the top of [create-image.ts](https://github.com/sagemathinc/cocalc/blob/master/src/packages/server/compute/cloud/google-cloud/create-image.ts).

For example, the following will create the x86_64 and arm64 Julia images with tag 1.10.1 in parallel, in about 5 minutes. Here's what a successful run looks like:

```sh
[prod3.test] kucalc-prod3-ctl-ws-3:~/kucalc/cluster2> c ssh hub-mentions
$ cd /cocalc/src/packages/server/ && node
> a = require('./dist/compute/cloud/google-cloud/create-image')
> await a.createImages({image:"julia", tag:'1.10.1'})
...

CREATED [ 'cocalc-julia-1-10-1-arm64', 'cocalc-julia-1-10-1' ]
DONE 5.081283333333333 minutes
[ 'cocalc-julia-1-10-1-arm64', 'cocalc-julia-1-10-1' ]
```

Also, to make the public [cocalc.com](http://cocalc.com) server recognize the new image.json file, be sure to click the "Reload Images" button in the advanced section when selecting a compute server:

![](.README.md.upload/paste-0.8430924123432122)

You can also visit the following URL's directly:

- [visit this url while signed in as an admin](https://cocalc.com/api/v2/compute/get-images?ttl=0), which triggers a cache clear of images.json.
- [and visit this url](https://cocalc.com/api/v2/compute/get-images-google?ttl=0), to clear the Google images cache.
- NOTE: even after clearing the cache, [cocalc.com](http://cocalc.com) might still take A LONG TIME until you see the difference.  The "cache" you're clearing is a record in the database, and individual hubs only update their view from the database record once per minute.  **Also, GitHub itself caches raw files for a long time.**  If you need to be very careful about what images.json you're using, change the actual URL to link to a specific version on GitHub via admin Settings.

Once you successfully create the new images, they should be an option when you click "Advanced" when creating a compute server (make sure to click the above link and refresh your browser). You can try the image out, and if it works well, as an admin click the button "Mark Google Cloud Image as Tested" at the bottom of a specific compute server's configuration modal. This causes the google cloud image to get labeled `tested : true`, at which point all users will see this image by default (without having to click "Advanced"). NOTE: any user can click "Advanced" and use images before they are marked as tested.

If building the image fails, the VM is left running for a while, and you can debug the problem. The problem is almost always "out of disk space", and the fix is to adjust the field `"minDiskSizeGb": xx` in images.json. In particular, if the size of the docker image gets a lot bigger, you need to adjust the field `"minDiskSizeGb": xx`. This is the smallest allowed disk for that image when creating a new VM. We want it to be small to save users money. On the other hand, things will break if it is too small. I don't know a good way to just compute its size as a function of the Docker image size, since the Docker image is compressed. Also, GPU/Nvidia drivers and the Ubuntu OS can complicate things.

