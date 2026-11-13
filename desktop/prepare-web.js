"use strict";
// ../web/dist klasörünü ./app içine kopyalar. Önce web'i derle: (cd ../web && npm run build)
const fs = require("node:fs");
const path = require("node:path");

const src = path.join(__dirname, "..", "web", "dist");
const dest = path.join(__dirname, "app");

if (!fs.existsSync(path.join(src, "index.html"))) {
  console.error("web/dist bulunamadı. Önce web'i derle:  cd ../web && npm install && npm run build");
  process.exit(1);
}
fs.rmSync(dest, { recursive: true, force: true });
fs.cpSync(src, dest, { recursive: true });
console.log(`web/dist -> desktop/app kopyalandı`);
