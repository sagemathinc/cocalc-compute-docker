/* Simple https server */

import express from "express";
import { createServer } from "https";
import genCert from "./gen-cert";

export default async function httpsServer() {
  const app = express();
  const cert = await genCert();
  console.log({ cert, app });
  const server = createServer(cert, app);

  return server;
}
