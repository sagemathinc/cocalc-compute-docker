#!/usr/bin/env node
const httpsServer = require("../dist/lib/https-server").default;

// use environment variables for all config.
//  PROXY_AUTH_TOKEN_FILE
//  PROXY_PORT
//  PROXY_HOST
//  PROXY_CONFIG
httpsServer();
