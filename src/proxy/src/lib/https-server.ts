/* Simple authenticated https server */

import genCert from "./gen-cert";
import debug from "debug";
import enableProxy from "./proxy";

const log = debug("proxy:http-server");

export default async function httpsServer({
  port = process.env.PROXY_PORT ? parseInt(process.env.PROXY_PORT) : 443,
  host = process.env.PROXY_HOST ?? "0.0.0.0",
  authTokenPath,
  configPath,
}: {
  port?: number;
  host?: string;
  authTokenPath?: string;
  configPath?: string;
} = {}) {
  log("creating https server", { port, host });
  if (configPath == null) {
    configPath = process.env["PROXY_CONFIG"];
  }
  if (configPath == null) {
    throw Error(
      "configPath must be defined or PROXY_CONFIG must be path to configuration json file",
    );
  }
  if (authTokenPath == null) {
    authTokenPath = process.env["PROXY_AUTH_TOKEN_FILE"];
  }

  // TODO: support letsencrypt option
  const cert = await genCert();
  // TODO: setup a redirect to port 443
  //const server = require('http').createServer(app);

  enableProxy({ cert, configPath, authTokenPath, port, host });
}
