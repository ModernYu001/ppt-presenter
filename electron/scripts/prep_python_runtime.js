const fs = require('fs');
const path = require('path');

const runtimeDir = process.env.PYTHON_RUNTIME_DIR;
if (!runtimeDir) {
  console.log('PYTHON_RUNTIME_DIR not set, skip bundling python runtime.');
  process.exit(0);
}

const src = path.resolve(runtimeDir);
const dst = path.resolve(__dirname, '..', 'python-runtime');

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

console.log(`Bundling python runtime from ${src} -> ${dst}`);
copyRecursive(src, dst);
