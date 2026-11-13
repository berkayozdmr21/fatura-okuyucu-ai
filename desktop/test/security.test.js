"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");

const { classifyOpen, isAppUrl, isNavigationAllowed, isPermissionAllowed } = require("../security");

const APP = "file:///C:/Program%20Files/Fatura/resources/app";

test("yalnızca uygulamanın kendi dosyalarına gezinilebilir", () => {
  assert.equal(isNavigationAllowed(`${APP}/index.html`, APP), true);
  assert.equal(isNavigationAllowed(`${APP}/index.html#/documents`, APP), true);
  assert.equal(isNavigationAllowed("https://evil.example/", APP), false);
  assert.equal(isNavigationAllowed("file:///C:/Windows/System32/config", APP), false);
  assert.equal(isNavigationAllowed("javascript:alert(1)", APP), false);
  assert.equal(isNavigationAllowed("not a url", APP), false);
});

test("isAppUrl: komşu klasör taklidi (app-evil) kabul edilmemeli", () => {
  // main.js dizin URL'sini sondaki '/' olmadan verir; politika bunu kendisi tamamlamalı
  assert.equal(isAppUrl(`${APP}-evil/index.html`, APP), false);
  assert.equal(isAppUrl(`${APP}/index.html`, APP), true);
  assert.equal(isNavigationAllowed(`${APP}-evil/index.html`, APP), false);
});

test("window.open sınıflandırması", () => {
  assert.equal(classifyOpen("blob:file:///1234-abcd"), "popup");
  assert.equal(classifyOpen("https://claude.ai/"), "external");
  assert.equal(classifyOpen("http://example.com"), "deny");
  assert.equal(classifyOpen("file:///etc/passwd"), "deny");
  assert.equal(classifyOpen("javascript:alert(1)"), "deny");
  assert.equal(classifyOpen("data:text/html,<script>1</script>"), "deny");
  assert.equal(classifyOpen("::::"), "deny");
});

test("hiçbir tarayıcı izni verilmez", () => {
  assert.equal(isPermissionAllowed(), false);
});
