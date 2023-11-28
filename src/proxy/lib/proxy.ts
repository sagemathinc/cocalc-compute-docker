import debug from "debug";
import type { Application } from "express";
import { createProxyServer } from "http-proxy";

const log = debug("proxy");

/* Example config:
[
  { path: "/api", target: "http://localhost:11434/api" },
  { path: "/", target: "http://localhost:8080", ws: true },
];
*/

export type Configuration = { path: string; target: string; ws?: boolean }[];

export default function createProxy(app: Application, config: Configuration) {
  log("creating proxy server");

  for (const { path, target, ws } of config) {
    const proxy = createProxyServer({ ws, target });
    log(`proxy: ${path} --> ${target}  ${ws ? "(+ websockets enabled)" : ""}`);
    proxy.on("error", (err) => {
      log(`proxy ${path} error: `, err);
    });
    app.use(path, proxy.web.bind(proxy));
    if (ws) {
      app.on("upgrade", proxy.ws.bind(proxy));
    }
  }
}
