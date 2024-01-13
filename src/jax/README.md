A good test from https://jax.readthedocs.io/en/latest/notebooks/quickstart.html

```py
import jax.numpy as jnp
from jax import grad, jit, vmap
from jax import random
key = random.PRNGKey(0)
x = random.normal(key, (10,))
print(x)
```