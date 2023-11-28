/* Simple authenticated https server */

import express from "express";
import { createServer } from "https";
import genCert from "./gen-cert";
import debug from "debug";
import { callback } from "awaiting";
import enableProxy from "./proxy";
import enableAuth from "./auth";
import type { Configuration } from "./proxy";
import { readFile } from "fs/promises";

const log = debug("http-server");

export default async function httpsServer({
  port = process.env.PORT ? parseInt(process.env.PORT) : 443,
  host = process.env.HOST ?? "0.0.0.0",
  authToken,
  config,
}: {
  port?: number;
  host?: string;
  authToken?: string;
  config?: Configuration;
} = {}) {
  log("creating https server", { port, host });
  if (config == null) {
    config = JSON.parse(await loadFromFile("PROXY_CONFIG"));
  }
  if (config == null) {
    throw Error("config must be defined");
  }
  if (authToken == null) {
    authToken = await loadFromFile("PROXY_AUTH_TOKEN_FILE");
  }
  const app = express();
  const cert = await genCert();
  const server = createServer(cert, app);

  if (authToken) {
    enableAuth(app, authToken);
  }
  enableProxy(app, config);

  log(`starting proxy server listening on ${host}:${port}`);
  await callback(server.listen.bind(server), port, host);

  return server;
}

async function loadFromFile(name) {
  const path = process.env[name];
  if (!path) {
    throw Error(`the environment variable '${name}' must be set`);
  }
  return (await readFile(path)).toString().trim();
}
