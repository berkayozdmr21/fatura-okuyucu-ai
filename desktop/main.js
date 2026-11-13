"use strict";
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { app, BrowserWindow, Menu, session, shell } = require("electron");

const { classifyOpen, isNavigationAllowed, isPermissionAllowed } = require("./security");

const APP_DIR = path.join(__dirname, "app");
const APP_DIR_URL = pathToFileURL(APP_DIR).href;
const INDEX = path.join(APP_DIR, "index.html");

const secureWebPreferences = {
  contextIsolation: true,
  nodeIntegration: false,
  sandbox: true,
  webSecurity: true,
  allowRunningInsecureContent: false,
};

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 480,
    minHeight: 560,
    title: "Fatura Okuyucu",
    backgroundColor: "#f6f7f9",
    webPreferences: { ...secureWebPreferences, preload: path.join(__dirname, "preload.js") },
  });

  win.webContents.on("will-navigate", (event, url) => {
    if (!isNavigationAllowed(url, APP_DIR_URL)) event.preventDefault();
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    switch (classifyOpen(url)) {
      case "popup":
        // Belge önizlemesi: kendi izole penceresinde, Node erişimi olmadan
        return { action: "allow", overrideBrowserWindowOptions: { webPreferences: { ...secureWebPreferences } } };
      case "external":
        void shell.openExternal(url);
        return { action: "deny" };
      default:
        return { action: "deny" };
    }
  });

  void win.loadFile(INDEX);
  return win;
}

// Tek örnek: ikinci kez açılırsa mevcut pencereyi öne getir
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    const [win] = BrowserWindow.getAllWindows();
    if (win) {
      if (win.isMinimized()) win.restore();
      win.focus();
    }
  });

  app.whenReady().then(() => {
    session.defaultSession.setPermissionRequestHandler((_wc, _permission, callback) => callback(isPermissionAllowed()));
    session.defaultSession.setPermissionCheckHandler(() => isPermissionAllowed());

    Menu.setApplicationMenu(
      Menu.buildFromTemplate([
        { label: "Uygulama", submenu: [{ role: "reload", label: "Yenile" }, { role: "quit", label: "Çık" }] },
        {
          label: "Görünüm",
          submenu: [
            { role: "zoomIn", label: "Yakınlaştır" },
            { role: "zoomOut", label: "Uzaklaştır" },
            { role: "resetZoom", label: "Normal boyut" },
            { role: "togglefullscreen", label: "Tam ekran" },
          ],
        },
      ]),
    );

    createWindow();
    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on("window-all-closed", () => {
    if (process.platform !== "darwin") app.quit();
  });
}
