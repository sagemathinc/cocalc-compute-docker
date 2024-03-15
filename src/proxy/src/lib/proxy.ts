import debug from "debug";
import { createProxyServer } from "http-proxy";
import { readFile } from "fs/promises";
import { watch } from "chokidar";
import enableAuth, { AUTH_PATH } from "./auth";
import { urlencoded } from "express";
import cookieParser from "cookie-parser";
import express, { Router } from "express";
import { createServer } from "https";
import { callback } from "awaiting";
import { pathToRegexp } from "path-to-regexp";

const log = debug("proxy:create-proxy");

export type Configuration = { path: string; target: string; ws?: boolean }[];

const ChokidarOpts = {
  persistent: true,
  followSymlinks: false,
  disableGlobbing: true,
  depth: 0,
  ignorePermissionErrors: true,
} as const;

export default async function createProxy({
  cert,
  configPath,
  authTokenPath,
  port,
  host,
}: {
  cert;
  configPath: string;
  authTokenPath?: string;
  port: number;
  host: string;
}) {
  log("creating proxy server with config from ", configPath);

  let disable: null | Function = null;
  let config: null | Configuration = null;
  let updating = false;
  const updateConfigPath = async () => {
    log("updating configuration from ", configPath);
    if (updating) {
      log("already updating -- will try again in a second");
      setTimeout(updateConfigPath, 1000);
      return;
    }
    try {
      updating = true;
      const app = express();
      app.on("error", (err) => {
        log("app ERROR", err);
      });

      const server = await createServer(cert, app);
      const router = Router();
      let newConfig: Configuration;
      try {
        newConfig = JSON.parse((await readFile(configPath)).toString().trim());
      } catch (err) {
        log("failed to load new config ", err);
        return;
      }
      log("loaded config from ", configPath, " -- ", newConfig);
      // weak equality check is fine for this
      if (JSON.stringify(config) == JSON.stringify(newConfig)) {
        log("no config change");
        return;
      }
      log("config changed");
      if (disable != null) {
        log("disabling old config before enabling new one");
        disable();
        disable = null;
      }
      config = newConfig;

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
          urlencoded({
            extended: true,
            type: "application/x-www-form-urlencoded",
          }),
        );
        // Use the cookie-parser middleware so req.cookies is defined.
        app.use(cookieParser());
        await enableAuth({ router, authTokenPath });
      } else {
        log(
          "auth token not enabled -- any client can connect to the proxied site",
        );
      }

      createRoutes(server, router, config);

      app.use(router);

      log(`starting proxy server listening on ${host}:${port}`);
      await callback(server.listen.bind(server), port, host);
      disable = async () => {
        log("closing server...");
        await server.close();
        log("server closed");
      };
    } finally {
      updating = false;
    }
  };

  const watcher = watch(configPath, ChokidarOpts);
  watcher.on("all", updateConfigPath);
  watcher.on("error", (err) => {
    log.debug(`error watching configPath '${configPath}' -- ${err}`);
  });
  await updateConfigPath();
}

function createRoutes(server, router, config) {
  const wsHandlers: { regexp; handler }[] = [];
  for (const { path, target, ws } of config) {
    const proxy = createProxyServer({ target });
    log(`proxy: ${path} --> ${target}  ${ws ? "(+ websockets enabled)" : ""}`);
    proxy.on("error", (err) => {
      log(`proxy ${path} error: `, err);
    });
    router.use(path, (req, res) => {
      proxy.web(req, res);
    });
    if (ws) {
      const wsProxy = createProxyServer({
        ws: true,
        target,
        prependPath: false,
      });
      wsHandlers.push({
        regexp: pathToRegexp(path + "(.*)"),
        handler: (req, socket, head) => {
          wsProxy.ws(req, socket, head);
        },
      });
    }
  }

  if (Object.keys(wsHandlers).length > 0) {
    server.on("upgrade", (req, socket, head) => {
      socket.on("error", (err) => {
        log("websocket upgrade socket error", err);
      });
      for (const { regexp, handler } of wsHandlers) {
        if (regexp.test(req.url)) {
          log(`websocket upgrade: FOUND handler matching url='${req.url}'`);
          handler(req, socket, head);
          return;
        }
      }
      log(`websocket upgrade: NO handler matched url='${req.url}'`);
      socket.write("HTTP/1.1 400 Bad Request\r\n\r\n");
      socket.destroy();
    });
  }
}
