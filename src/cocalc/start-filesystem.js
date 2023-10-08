#!/usr/bin/env node

/*
This is to be placed in /cocalc/src/packages/compute/ and run there.
Actually, it just needs @cocalc/compute to be require-able.
*/

process.env.BASE_PATH = process.env.BASE_PATH ?? "/";
process.env.API_SERVER = process.env.API_SERVER ?? "https://cocalc.com";
process.env.API_BASE_PATH = process.env.API_BASE_PATH ?? "/";

const util = require("util");
const exec = util.promisify(require("child_process").exec);

async function getFilesystemType(path) {
  try {
    const { stdout } = await exec(`df -T ${path} | awk 'NR==2 {print \$2}'`);
    return stdout.trim();
  } catch (error) {
    console.error(`exec error: ${error}`);
    return null;
  }
}

const { mountProject, jupyter, terminal } = require("@cocalc/compute");

const PROJECT_HOME = "/home/user";

async function main() {
  let unmount = null;
  let kernel = null;
  let term = null;
  const exitHandler = async () => {
    console.log("cleaning up...");
    process.removeListener("exit", exitHandler);
    process.removeListener("SIGINT", exitHandler);
    process.removeListener("SIGTERM", exitHandler);
    await unmount?.();
    process.exit();
  };

  process.on("exit", exitHandler);
  process.on("SIGINT", exitHandler);
  process.on("SIGTERM", exitHandler);

  const { apiKey } = require("@cocalc/backend/data");
  try {
    if (!process.env.PROJECT_ID) {
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

  console.log("Mounting project", process.env.PROJECT_ID, "at", PROJECT_HOME);
  try {
    // CRITICAL: Do NOT both mount the filesystem *and* and start terminals
    // in the same process.  Do one or the other.  Doing both as a non-root
    // user in docker at least leads to deadlocks.
    if ((await getFilesystemType(PROJECT_HOME)) != "fuse") {
      unmount = await mountProject({
        project_id: process.env.PROJECT_ID,
        path: PROJECT_HOME,
        options: { mountOptions: { allowOther: true } },
      });
    }
  } catch (err) {
    console.log("something went wrong ", err);
    exitHandler();
  }

  const info = () => {
    console.log("Success!");
    console.log(`Your home directory is mounted at ${PROJECT_HOME}`);
    console.log("\nPress Control+C to exit.");
  };

  info();
}

main();
