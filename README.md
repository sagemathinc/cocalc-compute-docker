# CoCalc Compute Docker

Docker image for adding remote compute capabilities to a CoCalc project.

URL: https://github.com/sagemathinc/cocalc-compute-docker

Run this image as follows to ensure that it has sufficient permissions to use FUSE to mount a filesystem. This won't work without these permissions:

```sh
docker run --name=cocalc-compute --cap-add=SYS_ADMIN --device /dev/fuse --security-opt apparmor:unconfined -d sagemathinc/cocalc-compute
```

To actually use it right now:

```sh
docker exec -it cocalc-compute bash
```

and then `cd /cocalc/src/packages/compute` and do the following (in two different shells):

## Example

Create an API*KEY in \_project settings*, where the api key is specific to the project you want to connect to.  Set all the env variables in your shell(s):

```sh
export BASE_PATH="/"
export API_KEY="sk-4xxxxxxxxxx0Q"
export API_SERVER="https://cocalc.com"
export API_BASE_PATH="/"
export PROJECT_ID="10f0e544-313c-4efe-8718-2142ac97ad11"
```

```sh
export DEBUG=cocalc:*
export DEBUG_CONSOLE=yes
```

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

Note that this Docker container is VERY bare bones and doesn't even have the Python Jupyter kernel in it.   You can install it as follows:

```sh
apt update && apt install python3-pip && pip install jupyter && python3 -m ipykernel install
```

