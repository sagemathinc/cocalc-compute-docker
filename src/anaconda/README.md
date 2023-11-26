# The Anaconda Image

This is an Anaconda image, using [micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html) \(a drop in replacement for `conda)` for self contained very fast installs.

Anaconda provides many Python packages that run together
in one Python environment, including [PyTorch](https://pytorch.org/), [Tensorflow](https://www.tensorflow.org/),
[SciPy](https://scipy.org/) and [SageMath](https://www.sagemath.org/).  It is the easiest way to install a wide
range of scientific tools into a single location. It also provides non\-Python software such as [Octave](https://octave.org/) and [Pari](https://pari.math.u-bordeaux.fr/).

It is very easy to install any packages you may need. Open a "Linux Terminal", select your compute server and type:

```sh
conda install packagename
```

Pretty much any scientific package you can think of is available! Search at https://anaconda.org/

If you need to add a channel do

```sh
conda config append channels 
```

