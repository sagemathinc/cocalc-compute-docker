#!/usr/bin/env node

console.log("Running @cocalc/compute-server...");

const path = require("path");
const { spawn } = require("child_process");

async function main() {
  const target = process.argv[2];

  if (!target) {
    console.error(`USAGE: ${process.argv[1]} install-path`);
    process.exit(1);
  }

  // remove the directory ${target}/src, since there could be extra
  // files there.
  await require("fs/promises").rm(path.join(target, "src"), {
    force: true,
    recursive: true,
  });

  const tarProcess = spawn("tar", [
    "-xzf",
    path.join(__dirname, "dist", "cocalc.tar.gz"),
    "--strip-components=1",
    "-C",
    target,
  ]);

  tarProcess.on("close", (code) => {
    if (code !== 0) {
      console.error(`Failed to extract cocalc.tar.gz to ${target}`, code);
      process.exit(1);
    } else {
      console.log(`Successfully extracted cocalc.tar.gz to ${target}`);
    }
  });
}

if (require.main === module) {
  main();
}
