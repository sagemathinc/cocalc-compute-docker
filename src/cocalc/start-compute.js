#!/usr/bin/env node

process.env.BASE_PATH = process.env.BASE_PATH ?? "/";
process.env.API_SERVER = process.env.API_SERVER ?? "https://cocalc.com";
process.env.API_BASE_PATH = process.env.API_BASE_PATH ?? "/";

const { manager } = require("@cocalc/compute");

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

  const { apiKey } = require("@cocalc/backend/data");
  try {
    if (!process.env.PROJECT_ID) {
      throw Error("You must set the PROJECT_ID environment variable");
    }

    if (!process.env.COMPUTE_SERVER_ID) {
      throw Error("You must set the COMPUTE_SERVER_ID environment variable");
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
    home: process.env.PROJECT_HOME,
    project_id: process.env.PROJECT_ID,
    compute_server_id: parseInt(process.env.COMPUTE_SERVER_ID),
    waitHomeFilesystemType:
      process.env.UNIONFS_UPPER && process.env.UNIONFS_LOWER
        ? "fuse.unionfs-fuse"
        : "fuse",
  });
  await M.init();
}

main();
