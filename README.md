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

### Docker

Support you want to be able to run docker inside the container. Include the option 

```sh
-v /var/run/docker.sock:/var/run/docker.sock
```

when you run docker \(as above\). Once you get a terminal in the container, install Docker:

```sh
 apt-get update && apt-get install -y docker.io
```

Then you can immediately fully use Docker.   

**Security Note:** that this is using the Docker daemon running on the host machine.  Thus only do this when you trust running anything via docker on the host machine, e.g., when the host machine is a dedicated VM specifically for this purpose.

### NVidia GPUs

If your host computer has a GPU \(so `nvidia-smi` should be there and show a GPU\), you can make it available by including this option on the command line when running Docker:

```sh
--gpus all 
```

When the container starts, type `nvidia-smi` to confirm the GPU is available.  You could see it in action by doing `pip install torch` then run this code in Python:

```py
import torch
import time

# define a tensor
a = torch.randn([10000, 10000])

# case for CUDA available (Assuming the previous cell returned 'True')
if torch.cuda.is_available():
    # move the tensor to GPU
    a = a.cuda()

    start = time.time()
    
    # perform an operation on the tensor
    a.sin_()
    
    print("Time taken when CUDA is available : ", time.time()-start)

# case for only CPU
else:
    start = time.time()
    
    # perform operation on the tensor
    a.sin_()
    
    print("Time taken when only CPU is available : ", time.time()-start)


```

