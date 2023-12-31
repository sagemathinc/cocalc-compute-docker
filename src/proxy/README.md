# Authenticating Local HTTPS Proxy

This is a simple and self\-contained https proxy server that is useful if you have one or more local HTTP servers and want to combine them together and serve the result over HTTPS with an autogenerated **self\-signed certificate** and an **authorization token**.

DEPENDENCIES: nodejs, openssl

You set four environment variables as below, then start it by typing `npx @cocalc/compute-server-proxy`. That's it.

```sh
export PROXY_AUTH_TOKEN_FILE=/auth_token
export PROXY_CONFIG=/proxy.json
export PROXY_HOSTNAME=0.0.0.0
export PROXY_PORT=443
npx @cocalc/compute-server-proxy
```

Here,

- `PROXY_PORT` -- port to serve on; 443 is a good choice, because this servers over https using a self-signed cert

- `PROXY_HOSTNAME` -- what the serve listens to. Use 0.0.0.0 to listen on all interfaces.

- `PROXY_AUTH_TOKEN_FILE` -- path to a file that contains the secret token. Make this file empty to turn off authentication.

- `PROXY_CONFIG` -- path to json file that contains the config. An example config is:

```json
[
  { "path": "/api", "target": "http://localhost:11434/api" },
  { "path": "/", "target": "http://localhost:8080", "ws": true }
]
```

The above config sends any path under /api to `http://localhost:11434/api` and everything else
to `http://localhost:8080`, and also proxies websockets
to `http://localhost:8080`. The path is [the path input to app.use for express.js](https://expressjs.com/en/4x/api.html#app.use).
The target is the URL of an http server.

If `PROXY_AUTH_TOKEN_FILE` is an empty file, then this program just proxied traffice to the servers you configured.
Otherwise, when a user first visits the site, they are
asked to enter the auth token:

![](.README.md.upload/paste-0.12375289236668618)

Once they enter the token, the AUTH\_TOKEN cookie is set in their browser, and they can then fully use the site.  Also, If they are visiting a specific url and hit the auth page, then authenticate, they are redirected to that url.

A user can alternatively set the query parameter ?auth\_token=... to the auth token.   In addition, if they want to use the site programmatically, they just have to set the AUTH\_TOKEN cookie directly, e.g.,

```sh
curl -v --cookie "AUTH_TOKEN=the-secret"  https://ollama.cocalc.cloud
```

## License

- AGPL \+ non\-commercial use.  Contact [help@cocalc.com](mailto:help@cocalc.com) if you want to use this commercially in your own software.

