const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let backendProcess = null;

function resolvePythonBin(projectRoot) {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const runtimePath = path.join(projectRoot, 'python-runtime');
  if (process.platform === 'win32') {
    const winPython = path.join(runtimePath, 'python.exe');
    if (fs.existsSync(winPython)) return winPython;
  }
  const unixCandidates = [
    path.join(runtimePath, 'bin', 'python3'),
    path.join(runtimePath, 'bin', 'python'),
    path.join(runtimePath, 'python3'),
    path.join(runtimePath, 'python'),
  ];
  for (const candidate of unixCandidates) {
    if (fs.existsSync(candidate)) return candidate;
  }
  return 'python3';
}

function resolveBackendExe(projectRoot) {
  const exeName = process.platform === 'win32' ? 'ppt-backend.exe' : 'ppt-backend';
  const exePath = path.join(projectRoot, 'backend-exe', exeName);
  if (fs.existsSync(exePath)) return exePath;
  return null;
}

function startBackend() {
  if (backendProcess) return;
  const projectRoot = path.resolve(__dirname, '../../..');
  const backendExe = process.env.BACKEND_EXE || resolveBackendExe(projectRoot);
  if (backendExe) {
    backendProcess = spawn(backendExe, [], {
      cwd: projectRoot,
      stdio: 'inherit',
      env: { ...process.env },
    });
  } else {
    const backendPath = process.env.BACKEND_SCRIPT || path.join(projectRoot, 'python', 'run_backend.py');
    const pythonBin = resolvePythonBin(projectRoot);
    backendProcess = spawn(pythonBin, [backendPath], {
      cwd: projectRoot,
      stdio: 'inherit',
      env: { ...process.env },
    });
  }

  backendProcess.on('exit', () => {
    backendProcess = null;
  });
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 860,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  const devServer = process.env.VITE_DEV_SERVER_URL;
  if (devServer) {
    win.loadURL(devServer);
  } else {
    win.loadFile(path.join(__dirname, '../../dist/index.html'));
  }
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});
