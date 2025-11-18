const { app, BrowserWindow } = require("electron");

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    frame: false,
    autoHideMenuBar: true,
    resizable: true,
    fullscreen: false,
    kiosk: false,
    webPreferences: {
      preload: __dirname + "/preload.js"
    }
  });

  win.loadURL("http://127.0.0.1:5000");

  win.webContents.on("did-finish-load", () => {
    win.webContents.insertCSS(`
      ::-webkit-scrollbar { display: none !important; }
      * { -webkit-app-region: no-drag; }

      #electron-drag-area {
        position: fixed;
        top: 0;
        left: 0;
        height: 32px;
        width: 100vw;
        -webkit-app-region: drag;
        background: transparent;
        z-index: 99999;
      }
    `);

    win.webContents.executeJavaScript(`
      if (!document.getElementById("electron-drag-area")) {
        const bar = document.createElement("div");
        bar.id = "electron-drag-area";
        document.body.appendChild(bar);
      }
    `);
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  app.quit();
});
