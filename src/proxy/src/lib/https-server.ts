/* Simple authenticated https server */

import express, { Router, urlencoded } from "express";
import cookieParser from "cookie-parser";
import { createServer } from "https";
import genCert from "./gen-cert";
import debug from "debug";
import { callback } from "awaiting";
import enableProxy from "./proxy";
import enableAuth, { AUTH_PATH } from "./auth";
import type { Configuration } from "./proxy";
import { readFile } from "fs/promises";

const log = debug("http-server");

export default async function httpsServer({
  port = process.env.PROXY_PORT ? parseInt(process.env.PROXY_PORT) : 443,
  host = process.env.PROXY_HOST ?? "0.0.0.0",
  authTokenPath,
  config,
}: {
  port?: number;
  host?: string;
  authTokenPath?: string;
  config?: Configuration;
} = {}) {
  log("creating https server", { port, host });
  if (config == null) {
    config = JSON.parse(await loadFromFile("PROXY_CONFIG"));
  }
  if (config == null) {
    throw Error("config must be defined");
  }
  if (authTokenPath == null) {
    authTokenPath = process.env["PROXY_AUTH_TOKEN_FILE"];
  }

  const app = express();
  const router = Router();
  const cert = await genCert();
  const server = createServer(cert, app);
  //const server = require('http').createServer(app);

  if (authTokenPath) {
    log(
      `enabling auth token for CoCalc proxy server -- path = '${authTokenPath}'`,
    );

    // Enable URL-encoded bodies, but ONLY for AUTH_PATH (!),
    // since otherwise this mangles the proxying of the target
    // sites, which is very, very bad in some cass, e.g.,
    // JupyterHub sign in is broken.
    router.use(
      AUTH_PATH,
      // type argument is just to minimize the impact
      urlencoded({ extended: true, type: "application/x-www-form-urlencoded" }),
    );
    // Use the cookie-parser middleware so req.cookies is defined.
    app.use(cookieParser());
    await enableAuth({ router, authTokenPath });
  } else {
    log("auth token not enabled -- any client can connect to the proxied site");
  }
  enableProxy({ router, server, config });

  app.use(router);

  log(`starting CoCalc proxy server listening on ${host}:${port}`);
  await callback(server.listen.bind(server), port, host);

  app.on("error", (err) => {
    log("app ERROR", err);
  });

  return server;
}

async function loadFromFile(name) {
  const path = process.env[name];
  if (!path) {
    throw Error(`the environment variable '${name}' must be set`);
  }
  return (await readFile(path)).toString().trim();
}
