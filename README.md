# CoCalc: Compute Server Image Management Repo

URL: https://github.com/sagemathinc/cocalc-compute-docker

Ultimately there will be sections below with step-by-step instructions
about how to update, build and test the compute server Docker images and npm pacckages we manage.

## Architectures: `x86_64` and `arm64`

I've taken great pains to ensure we fully support both architectures. This adds complexity and extra work at every step, unfortunately.

## How to update the cocalc npm package

To build the cocalc npm package and push it to npmjs with the label "test":

1. Update version of cocalc in this line in images.json: `{ "label": "test", "version": "1.8.1", "tag": "test", "tested": false }`
   e.g., from 1.8.1 to something newer than any tag, e.g., 1.8.3
2. `make cocalc && make push-cocalc`
3. Create a compute sever on cocalc.com and for the images check "Advanced" and then select the "test" version of cocalc. That compute server will then use this testing npm package.

When ready to release in prod, i.e., to push a package to npmjs with the label "latest":

1. Update this line in images.json `{ "label": "latest", "version": "1.8.2", "tag": "latest", "tested": true }`,
   e.g., from 1.8.2 to 1.8.4, which is newer than the one you just tested
2. `make COCALC_TAG=latest cocalc && make COCALC_TAG=latest push-cocalc`

NOTE: You should do the above on both `x86_64` and `arm64` architectures, as they are separate. There is code in the cocalc package that is platform specific.

Double check versions at

- https://www.npmjs.com/package/@cocalc/compute-server?activeTab=versions

and at

- https://www.npmjs.com/package/@cocalc/compute-server-arm64?activeTab=versions
