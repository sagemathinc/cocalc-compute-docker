#!/usr/bin/env node
/*
This nodejs script takes as command line parameter:
 - a file
 - a bucket name, e.g., 'mybucket'

It reads the file into memory, compresses it (in memory), then uploades the compressed
file to the given Google cloud storage bucket with the STANDARD storage class
using the @google-cloud/storage npm package.  Critically, it uses the standard storage
class irregardless of what the default storage class is for the bucket.

This is very important for writing redis dump files periodically to buckets that
might have a very non-STANDARD default storage class.  The compression saves a lot
of space, and since we write the dump file once per minute we save a huge amount
of money on early deletion fees.
*/

const fs = require("fs/promises");
const util = require("util");
const path = require("path");
const exec = util.promisify(require("child_process").exec);
const zlib = require("node:zlib");
const gzip = util.promisify(zlib.gzip);

async function ensureGoogleCloudInstalled(pkg) {
  try {
    require(pkg);
  } catch (_) {
    console.log(`Installing ${pkg}...`);
    await exec(`npm install ${pkg}`);
    console.log(`${pkg} installed successfully!`);
  }
}

async function uploadFileToGCS(filename, destFilename, bucketName) {
  await ensureGoogleCloudInstalled("@google-cloud/storage");
  const { Storage } = require("@google-cloud/storage");
  const storage = new Storage();

  try {
    const buffer = await fs.readFile(filename);
    // level 1 since any compression at all is great, but beyond 1 it hardly makes a difference, due
    // to redis dumps already being locally compressed. Plus this is much faster, hence less wasted cpu.
    const bufferGz = await gzip(buffer, { level: 1 });

    const bucket = storage.bucket(bucketName);
    const file = bucket.file(destFilename);

    // Create a writable stream for the Google Cloud Storage file,
    // which creates the new object with STANDARD storage class,
    // which is key!
    const stream = file.createWriteStream({
      metadata: {
        contentType: "application/gzip",
        storageClass: "STANDARD",
      },
      resumable: false,
    });

    // Stream events handlers
    await new Promise((resolve, reject) => {
      stream.on("error", reject);
      stream.on("finish", resolve);
      stream.end(bufferGz);
    });

    console.log(
      `Uploaded ${destFilename} to gs://${bucketName}/${destFilename}`,
    );
  } catch (err) {
    console.error("Failed to upload file:", err);
  }
}

function main() {
  if (process.argv.length !== 4) {
    console.error(
      `Gzips and uploads a file to Google Cloud Storage with the STANDARD
storage class set, irregardless of bucket defaults.
Assumes GOOGLE_APPLICATION_CREDENTIALS points to a service account file.`,
    );
    console.error(
      "Usage: node upload-gzstd.js <path/to/source> <gs://bucketName/path/to/target.gz>",
    );
    process.exit(1);
  }
  const filename = process.argv[2];
  let dest = process.argv[3];
  if (!dest.startsWith("gs://")) {
    console.error("target must start with gs://");
  }
  dest = dest.slice("gs://".length);
  i = dest.indexOf("/");
  let destFilename, bucketName;
  console.log({ i, dest });
  if (i == -1) {
    bucketName = dest;
    destFilename = "";
  } else {
    bucketName = dest.slice(0, i);
    destFilename = dest.slice(i + 1).trim();
  }
  if (!destFilename) {
    destFilename = path.basename(filename);
  }
  if (!destFilename.endsWith(".gz")) {
    destFilename += ".gz";
  }
  console.log({ filename, destFilename, bucketName });
  uploadFileToGCS(filename, destFilename, bucketName);
}

main();
