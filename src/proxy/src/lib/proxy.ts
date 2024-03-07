import debug from "debug";
import { createProxyServer } from "http-proxy";

const log = debug("proxy");

export type Configuration = { path: string; target: string; ws?: boolean }[];

export default function createProxy({
  server,
  router,
  config,
}: {
  router,
  server;
  config: Configuration;
}) {
  log("creating proxy server");

  for (const { path, target, ws } of config) {
    const proxy = createProxyServer({ ws, target });
    log(`proxy: ${path} --> ${target}  ${ws ? "(+ websockets enabled)" : ""}`);
    proxy.on("error", (err) => {
      log(`proxy ${path} error: `, err);
    });
    router.use(path, (req, res) => {
      proxy.web(req, res);
    });
    if (ws) {
      server.on("upgrade", (req, res, done) => {
        if (req.url.startsWith(path)) {
          proxy.ws(req, res, done);
        }
      });
    }
  }
  return router;
}

export function proxy2(config: Configuration) {
  for (const { target, ws } of config) {
    const proxy = createProxyServer({ ws, target });
    return proxy;
  }
  throw Error("bug");
}
