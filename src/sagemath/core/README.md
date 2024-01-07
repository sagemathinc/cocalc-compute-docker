Important note. Other containers are starting to depend on this one, and we want to try not to break them.

- cocalc-docker

- SageMath devcontainer -- https://github.com/sagemath/sage/pull/37029
  -- this assumes that there is a `SAGE_ROOT` in `/usr/local/sage/` without customization of `--prefix` or `--with-sage-venv`.
