/* Simple https server */

import express from "express";
import { createServer } from "https";
import genCert from "./gen-cert";
import debug from "debug";
import { callback } from "awaiting";
import createProxy from "./proxy";

const log = debug("http-server");

export default async function httpsServer({
  port = 443,
  host = "0.0.0.0",
}: {
  port?: number;
  host?: string;
} = {}) {
  log("creating https server", { port, host });
  const app = express();
  const cert = await genCert();
  const server = createServer(cert, app);
  const proxy = createProxy();

  app.all("*", proxy);

  log(`starting proxy server listening on ${host}:${port}`);
  await callback(server.listen.bind(server), port, host);

  return server;
}
