const fs = require('fs');
const path = require('path');

const srcDir = process.env.BACKEND_EXE_DIR;
if (!srcDir) {
  console.log('BACKEND_EXE_DIR not set, skip bundling backend exe.');
  process.exit(0);
}

const src = path.resolve(srcDir);
const dst = path.resolve(__dirname, '..', 'backend-exe');

function copyRecursive(srcPath, dstPath) {
  if (!fs.existsSync(srcPath)) return;
  if (!fs.existsSync(dstPath)) fs.mkdirSync(dstPath, { recursive: true });
  const entries = fs.readdirSync(srcPath, { withFileTypes: true });
  for (const entry of entries) {
    const s = path.join(srcPath, entry.name);
    const d = path.join(dstPath, entry.name);
    if (entry.isDirectory()) {
      copyRecursive(s, d);
    } else {
      fs.copyFileSync(s, d);
    }
  }
}

console.log(`Bundling backend exe from ${src} -> ${dst}`);
copyRecursive(src, dst);
