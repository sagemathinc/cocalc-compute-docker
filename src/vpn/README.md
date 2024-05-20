This works:

```sh
docker run --network host -v /cocalc:/cocalc -v /home/user:/home/user --privileged -it sagemathinc/wireguard:1.0 bash
```