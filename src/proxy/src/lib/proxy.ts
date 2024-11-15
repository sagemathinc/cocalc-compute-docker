import debug from "debug";
import { createProxyServer } from "./proxy-with-params";
import { readFile } from "fs/promises";
import { watch } from "chokidar";
import enableAuth, { AUTH_PATH } from "./auth";
import { urlencoded } from "express";
import cookieParser from "cookie-parser";
import express, { Router } from "express";
import { createServer } from "https";
import { callback } from "awaiting";
import { pathToRegexp } from "path-to-regexp";
import { COOKIE_NAME } from "./auth";
import { debounce } from "lodash";

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
  let isAuthCookieValid = (_req) => false;
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
        log("failed to load new config (disabling server) ", err);
        newConfig = [];
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

      if (!config.length) {
        // empty config, so do not bind to 443 and disable is empty.
        disable = () => {};
        return;
      }

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
        isAuthCookieValid = await enableAuth({ router, authTokenPath });
      } else {
        // probably never used (?)
        log(
          "auth token not enabled -- any client can connect to the proxied site",
        );
        isAuthCookieValid = (_req) => true;
      }

      createRoutes(server, router, config, isAuthCookieValid);

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
  // debounce reading file so don't read it while it is
  // being written resulting in corruption.  Client code
  // *should* always write a different file, then move
  // it onto config file which is atomic... but we do
  // not want to rely on that.
  watcher.on(
    "all",
    debounce(updateConfigPath, 1000, { leading: true, trailing: true }),
  );
  watcher.on("error", (err) => {
    log.debug(`error watching configPath '${configPath}' -- ${err}`);
  });
  await updateConfigPath();
}

function createRoutes(server, router, config, isAuthCookieValid) {
  const wsHandlers: { regexps; handler }[] = [];
  for (const { path, target, ws = true, options, wsOptions } of config) {
    const proxy = createProxyServer({ target, ...options, path });
    log(`proxy: ${path} --> ${target}  ${ws ? "(+ websockets enabled)" : ""}`);
    proxy.on("error", (err) => {
      log(`proxy ${path} error: `, err);
    });
    router.use(path, (req, res) => {
      // stripAuthCookieFromRequest(req);
      proxy.web(req, res);
    });
    if (ws) {
      const wsProxy = createProxyServer({
        ws: true,
        target,
        prependPath: false,
        ...wsOptions,
        path,
      });
      wsProxy.on("error", (err) => {
        log(`websocket proxy ${path} error: `, err);
      });
      wsHandlers.push({
        regexps: [pathToRegexp(path), pathToRegexp(path + "/(.*)")],
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
      if (!isAuthCookieValid(req)) {
        socket.write("HTTP/1.1 400 inavalid auth cookie\r\n\r\n");
        socket.destroy();
        return;
      }
      for (const { regexps, handler } of wsHandlers) {
        for (const regexp of regexps) {
          if (regexp.test(req.url)) {
            log(`websocket upgrade: FOUND handler matching url='${req.url}'`);
            // stripAuthCookieFromRequest(req);
            handler(req, socket, head);
            return;
          }
        }
      }
      log(`websocket upgrade: NO handler matched url='${req.url}'`);
      socket.write("HTTP/1.1 400 Bad Request\r\n\r\n");
      socket.destroy();
    });
  }
}

// Disabled for now.  This would be a nice added measure of security,
// but it's not critical, given that the registration token is known
// to the compute server anyways. It's right there on the filesystem.
// Also this causes trouble randomly for some servers (e.g., pluto).

// // SECURITY: We do NOT include the auth cookie in what we
// // send to the target, so one proxied service can't gain
// // access to another one.
// function stripAuthCookieFromRequest(req) {
//   if (req.headers["cookie"] != null) {
//     req.headers["cookie"] = stripAuthCookie(req.headers["cookie"]);
//   }
// }

// We do not use this because it breaks things in a bunch of cases still.
// basically the stripping must be indirectly impacting how requests work
// so that they aren't authenticated, and everything is broken.
export function stripAuthCookie(cookie: string): string {
  if (cookie == null) {
    return cookie;
  }
  const v: string[] = [];
  for (const c of cookie.split(";")) {
    const z = c.split("=");
    if (z[0].trim() == COOKIE_NAME) {
      // do not include it in v, which will
      // be the new cookies values after going through
      // the proxy.
    } else {
      v.push(c);
    }
  }
  return v.join(";");
}
