#!/usr/bin/env node

/*

node get-tag.js images.json image-name

outputs the version for the newest versioni n the images.json
file for the given image name.

If the version isn't explicitly specified, the tag is output
*/

const { readFileSync } = require("fs");

const imagesJson = process.argv[2];
const imageName = process.argv[3];

// imageTag - this may be omitted in which case we take the last one
// This is for npm where there's tags like "test" and "latest", that
// map to a version, i.e., we are not trying to get the latest tag in this case,
// but the npm version.
const imageTag = process.argv[4];

const IMAGES = JSON.parse(readFileSync(imagesJson).toString());
if (IMAGES[imageName] == null) {
  throw Error("there is no version info about '" + imageName + "'");
}

const { versions } = IMAGES[imageName];
if (!imageTag) {
  const data = versions[versions.length - 1];
  console.log(data.version ?? data.tag);
} else {
  // version for last matching tag
  for (const data of versions.reverse()) {
    if (data.tag == imageTag) {
      console.log(data.version);
      break;
    }
  }
}
