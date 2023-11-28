/* Simple authenticated https server */

import express from "express";
import { createServer } from "https";
import genCert from "./gen-cert";
import debug from "debug";
import { callback } from "awaiting";
import createProxy from "./proxy";
import enableAuth from "./auth";

const log = debug("http-server");

const AUTH_TOKEN = process.env.AUTH_TOKEN ?? "";
if (process.env.AUTH_TOKEN) {
  delete process.env.AUTH_TOKEN;
}

export default async function httpsServer({
  port = process.env.PORT ? parseInt(process.env.PORT) : 443,
  host = process.env.HOST ?? "0.0.0.0",
  // If given, user must visit https://host:port/authToken once to set a cookie.
  // They are then redirected to https://host:port/
  authToken = AUTH_TOKEN,
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
