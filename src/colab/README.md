# Colab-like environment

To update, run the following in a fresh Colab notebook:

```
! pip freeze > env.txt
```

and the download the file and put it in here

```
from google.colab import files
files.download('env.txt')
```
