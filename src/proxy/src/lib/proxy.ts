import debug from "debug";
import { createProxyServer } from "http-proxy";
import { readFile } from "fs/promises";
import { watch } from "chokidar";

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
  server,
  router,
  configPath,
}: {
  router;
  server;
  configPath: string;
}) {
  log("creating proxy server");

  let disable: null | Function = null;
  const updateConfigPath = async () => {
    log("updating configuration from ", configPath);
    if (disable != null) {
      disable();
    }
    const config: Configuration = JSON.parse(
      (await readFile(configPath)).toString().trim(),
    );
    log("loaded config", config);
    disable = createRoutes(server, router, config);
  };

  const watcher = watch(configPath, ChokidarOpts);
  watcher.on("all", updateConfigPath);
  watcher.on("error", (err) => {
    log.debug(`error watching configPath '${configPath}' -- ${err}`);
  });
  await updateConfigPath();

  return router;
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
