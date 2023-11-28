#!/usr/bin/env node
const httpsServer = require("../dist/lib/https-server").default;
const { readFileSync } = require("fs");

let authToken = "";
if (process.env.AUTH_TOKEN_FILE) {
  // NOTE: if can't read from file, will get error and no server. That's better
  // than a server with no auth!
  authToken = readFileSync(process.env.AUTH_TOKEN_FILE).toString().trim();
} else {
  authToken = "";
}

httpsServer({ authToken });
