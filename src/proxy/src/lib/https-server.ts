/* Simple authenticated https server */

import express, { Router, urlencoded } from "express";
import cookieParser from "cookie-parser";
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
  port = process.env.PROXY_PORT ? parseInt(process.env.PROXY_PORT) : 443,
  host = process.env.PROXY_HOST ?? "0.0.0.0",
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
  const router = Router();
  const cert = await genCert();
  const server = createServer(cert, app);
  //const server = require('http').createServer(app);

  if (authToken) {
    // Enable URL-encoded bodies
    app.use(urlencoded({ extended: true }));
    // Use the cookie-parser middleware so req.cookies is defined.
    app.use(cookieParser());
    enableAuth({ router, authToken });
  }
  enableProxy({ router, server, config });

  app.use(router);

  log(`starting CoCalc proxy server listening on ${host}:${port}`);
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
