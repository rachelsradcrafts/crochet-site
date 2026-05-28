const fs = require("fs");
const path = require("path");

const imagesRoot = path.join(__dirname, "public", "images");
const outputFile = path.join(__dirname, "public", "gallery-data.js");

const allowedExtensions = new Set([".jpg", ".jpeg", ".png", ".webp", ".gif"]);

function displayNameFromFolder(folderName) {
  return folderName
    .replace(/[-_]+/g, " ")
    .replace(/\b\w/g, letter => letter.toUpperCase());
}

function idFromFolder(folderName) {
  return folderName
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function readPrice(folderPath) {
  const priceFile = path.join(folderPath, "price.txt");

  if (!fs.existsSync(priceFile)) {
    return "Price TBD";
  }

  const price = fs.readFileSync(priceFile, "utf8").trim();

  if (price.length === 0) {
    return "Price TBD";
  }

  if (price.startsWith("$")) {
    return price;
  }

  return "$" + price;
}

const items = fs
  .readdirSync(imagesRoot, { withFileTypes: true })
  .filter(entry => entry.isDirectory())
  .map(entry => {
    const folder = entry.name;
    const folderPath = path.join(imagesRoot, folder);

    const imageFiles = fs
  .readdirSync(folderPath, { withFileTypes: true })
  .filter(file => file.isFile())
  .map(file => file.name)
  .filter(fileName => allowedExtensions.has(path.extname(fileName).toLowerCase()));

const images = imageFiles
  .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));

const gitLogFile = path.join(folderPath, imageFiles[0]);

let newestImageTime = 0;

try {
  const { execSync } = require("child_process");

  newestImageTime = Number(
    execSync(
      `git log -1 --format=%ct -- "${gitLogFile}"`,
      { encoding: "utf8" }
    ).trim()
  );
} catch {
  newestImageTime = 0;
}

   return {
  id: idFromFolder(folder),
  name: displayNameFromFolder(folder),
  folder,
  price: readPrice(folderPath),
  newestImageTime,
  images
};
  })
  .filter(item => item.images.length > 0);

const fileContents =
  "window.galleryItems = " + JSON.stringify(items, null, 2) + ";\n";

fs.writeFileSync(outputFile, fileContents);

console.log(`Generated ${outputFile}`);
console.log(`Found ${items.length} item folders.`);