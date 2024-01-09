#!/usr/bin/env node

/*

node get-tag.js images.json image-name

outputs the tag for the newest version in the images.json file
for the given image name
*/

const { readFileSync } = require("fs");

const imagesJson = process.argv[2];
const imageName = process.argv[3];

const IMAGES = JSON.parse(readFileSync(imagesJson).toString());
const { versions } = IMAGES[imageName];
console.log(versions[versions.length - 1].tag);
