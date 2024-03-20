import { createProxyServer as createProxyServer0 } from "http-proxy";
import { EventEmitter } from "events";
import TTLCache from "@isaacs/ttlcache";
import debug from "debug";
import { pathToRegexp, Key } from "path-to-regexp";

const TTL_MS = 5 * 60 * 1000; // 5 minutes
const MAX = 200;

const log = debug("proxy:proxy-with-params");

function isDynamicTarget(target: string) {
  return target.includes("[") && target.includes("]");
}

export function createProxyServer(options) {
  const { target } = options;
  if (!isDynamicTarget(target)) {
    log("using non-dynamic proxy for ", { target });
    return createProxyServer0(options);
  }
  log("using dynamic proxy for ", { target });
  // create dynamic proxy server that depends on params in req
  return new Proxy(options);
}

class Proxy extends EventEmitter {
  private options;
  private proxies = new TTLCache({ max: MAX, ttl: TTL_MS });

  constructor(options) {
    super();
    this.options = options;
  }

  private getProxy = (params) => {
    const key = JSON.stringify(params);
    if (this.proxies.has(key)) {
      return this.proxies.get(key);
    }
    let { target } = this.options;
    log("dynamic proxy NOT in cache, so creating", {
      target,
      params,
      options: this.options,
    });
    for (const name in params) {
      target = replace_all(target, `[${name}]`, params[name]);
    }
    if (isDynamicTarget(target)) {
      // not every pattern was substituted, so this is probably NOT going to work.
      log("WARNING: after param substitution not all patterns replaced", {
        target,
        params,
        path: this.options.path,
      });
    }
    log("new target", { target });
    const proxy = createProxyServer0({ ...this.options, target });
    proxy.on("error", (...args) => {
      this.emit("error", ...args);
    });
    this.proxies.set(key, proxy);
    return proxy;
  };

  web = (req, res, options?) => {
    this.getProxy(req.params).web(req, res, options);
  };

  ws = (req, socket, head, options?) => {
    this.getProxy(getParams(this.options.path, req.url)).ws(
      req,
      socket,
      head,
      options,
    );
  };
}

export function replace_all(
  s: string,
  search: string,
  replace: string,
): string {
  return s.split(search).join(replace);
}

// For websocket upgrade requests, the req.params field
// does NOT get filled in by express.js.  So I studied
// the implementation in express of this functionality at
//    https://github.com/expressjs/express/blob/master/lib/router/layer.js
// and reimplemented from scratch here. That's the only
// non-hack way I could think of to do this in a way that
// is provides consistent results.  This is absolutely needed,
// e.g., for proxying jupyterlab.
export function getParams(
  path: string,
  url: string,
): { [name: string]: string } {
  let keys: Key[] = [];
  let regexp = pathToRegexp(path, keys);
  let match = regexp.exec(url);
  if (!match) {
    keys = [];
    regexp = pathToRegexp(path + "/(.*)", keys);
    match = regexp.exec(url);
  }
  const params: { [name: string]: string } = {};
  if (!match) {
    return params;
  }
  for (let i = 1; i < match.length; i++) {
    const key = keys[i - 1];
    const prop = key.name;
    try {
      const val = decodeParam(match[i]);
      if (val !== undefined || params[prop] == null) {
        params[prop] = val;
      }
    } catch (err) {
      log("WARNING - issue decoding param", { path, url, err });
    }
  }
  return params;
}

function decodeParam(val) {
  if (typeof val !== "string" || val.length === 0) {
    return val;
  }
  return decodeURIComponent(val);
}
