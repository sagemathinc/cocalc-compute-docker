# CoCalc: Compute Docker Image

Docker image for adding remote compute capabilities to a CoCalc project.

URL: https://github.com/sagemathinc/cocalc-compute-docker

Run this image as follows to ensure that it has sufficient permissions to use FUSE to mount a filesystem. This won't work without these permissions.  Also, fill in the API\_KEY, PROJECT\_ID, and IPYNB\_PATH below.

```sh
docker run  \
   -e API_KEY=sk-4xxxxxxxxxxxx000Q \
   -e PROJECT_ID=ab3c2e56-32c4-4fa5-a3ee-6fd980d10fbf \
   -e IPYNB_PATH=myfile.ipynb  \
   -e TERM_PATH=term.term \
   --cap-add=SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined \
   sagemathinc/compute-python3
```

- Get the API_KEY in project settings.
- Open the Ipython notebook in your browser.  The path is relative to your home directory.

If you want to see a lot of logging involving Jupyter, add

```sh
-e DEBUG=cocalc:*
```

or for logging as much as possible: `-e DEBUG=*` . 

### Mounting the project home directory

Mount the project's HOME directory at /tmp/project by
running this code in nodejs after setting all of the above environment variables.

```js
await require("@cocalc/compute").mountProject({
  project_id: process.env.PROJECT_ID,
  path: "/tmp/project",
});
0;
```

### Jupyter

You should open the notebook Untitled.ipynb on [cocalc.com](http://cocalc.com).
Then set all the above env variables in another terminal and run the following code in node.js. **Running of that Jupyter notebook will then switch to your local machine.**

```js
await require("@cocalc/compute").jupyter({
  project_id: process.env.PROJECT_ID,
  path: "Untitled.ipynb",
  cwd: "/tmp/project",
});
0;
```

