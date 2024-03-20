import { createProxyServer as createProxyServer0 } from "http-proxy";
import { EventEmitter } from "events";

export function createProxyServer(options) {
  const { target } = options;
  if (!target.includes("[") && !target.includes("]")) {
    return createProxyServer0(options);
  }
  // create dynamic proxy server that depends on params in req
  return new Proxy(options);
}

class Proxy extends EventEmitter {
  private options;
  private proxies: { [key: string]: ReturnType<createProxyServer0> } = {};

  constructor(options) {
    super();
    this.options = options;
  }

  private getProxy = (params) => {
    const key = JSON.stringify(params);
    if (this.proxies[key]) {
      return this.proxies[key];
    }
    let { target } = this.options;
    for (const name in params) {
      target = replace_all(target, `[${name}]`, params[name]);
    }
    const proxy = createProxyServer0({ ...this.options, target });
    proxy.on("error", (...args) => {
      this.emit("error", ...args);
    });
    this.proxies[key] = proxy;
    return proxy;
  };

  web = (req, res, options?) => {
    this.getProxy(req.params).web(req, res, options);
  };

  ws = (req, socket, head, options?) => {
    this.getProxy(req.params).ws(req, socket, head, options);
  };
}

export function replace_all(
  s: string,
  search: string,
  replace: string,
): string {
  return s.split(search).join(replace);
}
