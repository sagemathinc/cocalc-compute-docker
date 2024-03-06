import debug from "debug";
import type { Application } from "express";
import { Router } from "express";
import { createProxyServer } from "http-proxy";

const log = debug("proxy");

export type Configuration = { path: string; target: string; ws?: boolean }[];

export default function createProxy({
  app,
  server,
  config,
}: {
  app: Application;
  config: Configuration;
  server;
}) {
  log("creating proxy server");
  const router = Router();

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
  app.use(router);
}

export function proxy2(config: Configuration) {
  for (const { target, ws } of config) {
    const proxy = createProxyServer({ ws, target });
    return proxy;
  }
  throw Error("bug");
}
