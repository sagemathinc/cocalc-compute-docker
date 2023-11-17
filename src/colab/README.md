# Colab-like environment

To update, run the following in a fresh Colab notebook:

```bash
! pip freeze > pip.txt
```

and the download the file and put it in here

```bash
from google.colab import files
files.download('pip.txt')
```

Similarly, to get the `apt.txt` file, run

```bash
! apt list --installed > apt.txt
```
