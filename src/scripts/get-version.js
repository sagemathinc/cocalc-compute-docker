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

const IMAGES = JSON.parse(readFileSync(imagesJson).toString());
const { versions } = IMAGES[imageName];
const data = versions[versions.length - 1];
console.log(data.version ?? data.tag);
