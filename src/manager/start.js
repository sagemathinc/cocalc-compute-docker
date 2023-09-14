#!/usr/bin/env node

process.env.BASE_PATH = process.env.BASE_PATH ?? "/";
process.env.API_SERVER = process.env.API_SERVER ?? "https://cocalc.com";
process.env.API_BASE_PATH = process.env.API_BASE_PATH ?? "/";

const { jupyter, terminal } = require("@cocalc/compute");

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
  let kernel = null;
  let term = null;
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

  // TODO...
  while ((await getFilesystemType(PROJECT_HOME)) != "fuse") {
    console.log(`Waiting for ${PROJECT_HOME} to be mounted`);
    await delay(3000);
  }

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

  try {
    if (process.env.TERM_PATH) {
      console.log("Connecting to", process.env.TERM_PATH);
      term = await terminal({
        project_id: process.env.PROJECT_ID,
        path: process.env.TERM_PATH,
        cwd: PROJECT_HOME,
      });
    }

    if (process.env.IPYNB_PATH) {
      console.log("Connecting to", process.env.IPYNB_PATH);
      kernel = await jupyter({
        project_id: process.env.PROJECT_ID,
        path: process.env.IPYNB_PATH,
        cwd: PROJECT_HOME,
      });
    }
  } catch (err) {
    console.log("something went wrong ", err);
    exitHandler();
  }

  const info = () => {
    console.log("Success!");

    if (process.env.IPYNB_PATH) {
      console.log(
        `Your notebook ${process.env.IPYNB_PATH} should be running in this container.`,
      );
      console.log(
        `  ${process.env.API_SERVER}/projects/${process.env.PROJECT_ID}/files/${process.env.IPYNB_PATH}`,
      );
    }

    if (process.env.TERM_PATH) {
      console.log(
        `Your terminal ${process.env.TERM_PATH} should be running in this container.`,
      );
      console.log(
        `  ${process.env.API_SERVER}/projects/${process.env.PROJECT_ID}/files/${process.env.TERM_PATH}`,
      );
    }

    console.log("\nPress Control+C to exit.");
  };

  info();
}

main();
