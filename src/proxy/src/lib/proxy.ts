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
  const app = express();
  app.on("error", (err) => {
    log("app ERROR", err);
  });

  const server = await createServer(cert, app);
  const router = Router();

  let disable: null | Function = null;
  let config: null | Configuration = null;
  const updateConfigPath = async () => {
    log("updating configuration from ", configPath);
    if (disable != null) {
      disable();
    }
    const newConfig: Configuration = JSON.parse(
      (await readFile(configPath)).toString().trim(),
    );
    log("loaded config from ", configPath, " -- ", newConfig);
    // weak equality check is fine for this
    if (JSON.stringify(config) == JSON.stringify(newConfig)) {
      log("no config change");
      return;
    }
    log("config changed");
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

    disable = createRoutes(server, router, config);
  };

  const watcher = watch(configPath, ChokidarOpts);
  watcher.on("all", updateConfigPath);
  watcher.on("error", (err) => {
    log.debug(`error watching configPath '${configPath}' -- ${err}`);
  });
  await updateConfigPath();

  app.use(router);

  log(`starting CoCalc proxy server listening on ${host}:${port}`);
  await callback(server.listen.bind(server), port, host);
}

function createRoutes(server, router, config) {
  const disabled = { current: false };
  const wsHandlers: { [path: string]: any } = {};
  for (const { path, target, ws } of config) {
    const proxy = createProxyServer({ ws, target });
    log(`proxy: ${path} --> ${target}  ${ws ? "(+ websockets enabled)" : ""}`);
    proxy.on("error", (err) => {
      log(`proxy ${path} error: `, err);
    });
    router.use(path, (req, res, next) => {
      if (disabled.current) {
        next();
      } else {
        proxy.web(req, res);
      }
    });
    if (ws != null) {
      wsHandlers[path] = (req, res, done) => {
        if (req.url.startsWith(path)) {
          proxy.ws(req, res, done);
        }
      };
    }
  }

  let handleUpgrade: null | Function = null;
  if (Object.keys(wsHandlers).length > 0) {
    const handleUpgrade = (req, res, done) => {
      for (const path in wsHandlers) {
        if (req.url.startsWith(path)) {
          wsHandlers[path].ws(req, res, done);
          return;
        }
      }
    };
    server.on("upgrade", handleUpgrade);
  }

  return () => {
    disabled.current = true;
    if (handleUpgrade != null) {
      server.removeListener("upgrade", handleUpgrade);
    }
  };
}
