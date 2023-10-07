#!/usr/bin/env node

process.env.BASE_PATH = process.env.BASE_PATH ?? "/";
process.env.API_SERVER = process.env.API_SERVER ?? "https://cocalc.com";
process.env.API_BASE_PATH = process.env.API_BASE_PATH ?? "/";

const { manager } = require("@cocalc/compute");

const PROJECT_HOME = "/home/user";

const util = require("util");
const exec = util.promisify(require("child_process").exec);
function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}
async function getFilesystemType(path) {
  try {
    const { stdout } = await exec(`df -T ${path} | awk 'NR==2 {print \$2}'`);
    return stdout.trim();
  } catch (error) {
    console.error(`exec error: ${error}`);
    return null;
  }
}

async function main() {
  const exitHandler = async () => {
    console.log("cleaning up...");
    process.removeListener("exit", exitHandler);
    process.removeListener("SIGINT", exitHandler);
    process.removeListener("SIGTERM", exitHandler);
    process.exit();
  };

  process.on("exit", exitHandler);
  process.on("SIGINT", exitHandler);
  process.on("SIGTERM", exitHandler);

  while ((await getFilesystemType(PROJECT_HOME)) != "fuse") {
    console.log(`Waiting for ${PROJECT_HOME} to be mounted`);
    await delay(3000);
  }

  const { apiKey } = require("@cocalc/backend/data");
  try {
    if (!process.env.PROJECT_ID) {
      throw Error("You must set the PROJECT_ID environment variable");
    }

    if (!process.env.COMPUTE_SERVER_ID) {
      throw Error("You must set the PROJECT_ID environment variable");
    }

    if (!apiKey) {
      throw Error("You must set the API_KEY environment variable");
    }
  } catch (err) {
    const help = () => {
      console.log(err.message);
      console.log(
        "See https://github.com/sagemathinc/cocalc-compute-docker#readme",
      );
    };
    help();
    setInterval(help, 5000);
    return;
  }

  const M = manager({
    project_id: process.env.PROJECT_ID,
    compute_server_id: process.env.COMPUTE_SERVER_ID,
  });
  await M.init();
}

main();
