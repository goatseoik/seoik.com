/* Bump the version whenever an app-shell file changes. */
"use strict";
const CACHE_PREFIX = "seoik-app-";
const CACHE_NAME = CACHE_PREFIX + "v33";
const BASE = new URL("./", self.location.href);
const FILES = [
  "index.html",
  "math/index.html",
  "math/data.js",
  "math/exam-sets.js",
  "math/transcribed-2026-06.js",
  "math/transcribed-2025-06.js",
  "math/transcribed-2025-09.js",
  "math/transcribed-2026-09.js",
  "math/transcribed-2026-06-mixed.js",
  "math/transcribed-2025-06-mixed.js",
  "math/transcribed-2025-09-mixed.js",
  "math/transcribed-2026-09-mixed.js",
  "math/transcribed-oct-geometry.js",
  "math/transcribed-2025-10-algebra.js",
  "math/transcribed-2026-10-algebra.js",
  "math/practice-pools.js",
  "math/practice-extra.js",
  "math/transcribed-2026-03-grade2.js",
  "math/math.css",
  "math/math.js",
  "math/questions.json",
  "math/variants.json",
  "서익닷컴.html",
  "manifest.webmanifest",
  "pwa.js",
  "pwa.css",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/apple-touch-icon.png"
].map(path => new URL(path, BASE).href);
const SHELL = new URL("index.html", BASE).href;

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(FILES.map(url => new Request(url, { cache: "reload" })));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
      .map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== BASE.origin) return;
  // Ignore query strings for the public app shell; never intercept auth/API data.
  url.search = "";
  url.hash = "";
  const key = url.href === BASE.href ? SHELL : url.href;
  const mathImage = url.pathname.startsWith(BASE.pathname + "math/assets/") && /^[-\w]+\.png$/.test(url.pathname.split("/").pop());
  if (!FILES.includes(key) && !mathImage) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(key);
    if (request.mode !== "navigate" && cached) return cached;
    try {
      const response = await fetch(request);
      if (response.ok && response.type !== "opaque" && !response.redirected) {
        await cache.put(key, response.clone()).catch(() => {});
      }
      return response;
    } catch (error) {
      if (cached) return cached;
      throw error;
    }
  })());
});
