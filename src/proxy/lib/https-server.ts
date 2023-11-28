/* Simple authenticated https server */

import express from "express";
import { createServer } from "https";
import genCert from "./gen-cert";
import debug from "debug";
import { callback } from "awaiting";
import createProxy from "./proxy";
import enableAuth from "./auth";

const log = debug("http-server");

export default async function httpsServer({
  port = process.env.PORT ? parseInt(process.env.PORT) : 443,
  host = process.env.HOST ?? "0.0.0.0",
  authToken = "",
}: {
  port?: number;
  host?: string;
  authToken?: string;
} = {}) {
  log("creating https server", { port, host });
  const app = express();
  const cert = await genCert();
  const server = createServer(cert, app);

  if (authToken) {
    enableAuth(app, authToken);
  }

  const proxyHandler = createProxy();
  app.all("*", proxyHandler);

  log(`starting proxy server listening on ${host}:${port}`);
  await callback(server.listen.bind(server), port, host);

  return server;
}
