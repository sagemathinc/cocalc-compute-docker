import debug from "debug";
import { createProxyServer } from "http-proxy";

const log = debug("proxy");

export default function createProxy() {
  log("creating proxy server");

  const proxy = createProxyServer({
    ws: false,
    target: "http://localhost:8080",
  });
  proxy.on("error", (err) => {
    log("proxy error: ", err);
  });

  const apiProxy = createProxyServer({
    ws: false,
    target: "http://localhost:11434/api",
  });
  apiProxy.on("error", (err) => {
    log("proxy error: ", err);
  });

  return (req, res) => {
    const v = req.url.split("/");
    if (v[1] == "api") {
      apiProxy.web(req, res);
    } else {
      proxy.web(req, res);
    }
  };
}
