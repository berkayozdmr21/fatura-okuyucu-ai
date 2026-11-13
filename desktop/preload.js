"use strict";
const { contextBridge } = require("electron");

// Sayfaya yalnızca salt okunur, zararsız bilgi açılır. Web arayüzü bunu istemci türünü ("desktop") anlamak için kullanır.
contextBridge.exposeInMainWorld("faturaDesktop", Object.freeze({ platform: process.platform }));
