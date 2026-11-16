const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const test = require("node:test");
const vm = require("node:vm");

// Exercise the worker's cache lifecycle without browser or package dependencies.
function worker(base = "https://example.test/seoik.com/") {
  const listeners = {};
  const stores = new Map();
  const requests = [];
  let offline = false;
  let body = "online";
  let claimed = false;
  let skipped = false;
  const key = request => typeof request === "string" ? request : request.url;
  const fetch = async request => {
    requests.push(request);
    if (offline) throw new TypeError("Offline");
    return new Response(body);
  };
  const caches = {
    async open(name) {
      if (!stores.has(name)) stores.set(name, new Map());
      const store = stores.get(name);
      return {
        async match(request) { return store.get(key(request))?.clone(); },
        async put(request, response) { store.set(key(request), response.clone()); },
        async addAll(list) {
          const responses = await Promise.all(list.map(fetch));
          list.forEach((request, index) => store.set(key(request), responses[index]));
        }
      };
    },
    async keys() { return [...stores.keys()]; },
    async delete(name) { return stores.delete(name); }
  };
  vm.runInNewContext(readFileSync(require.resolve("../sw.js"), "utf8"), {
    self: {
      location: { href: base + "sw.js" },
      addEventListener(name, listener) { listeners[name] = listener; },
      clients: { async claim() { claimed = true; } },
      async skipWaiting() { skipped = true; }
    },
    URL, Request, caches, fetch
  });
  return {
    stores, caches, requests,
    setOffline(value) { offline = value; },
    setBody(value) { body = value; },
    get claimed() { return claimed; },
    get skipped() { return skipped; },
    lifecycle(name) {
      let result;
      listeners[name]({ waitUntil(promise) { result = promise; } });
      return result;
    },
    request(path, { mode = "navigate", method = "GET" } = {}) {
      let result;
      listeners.fetch({
        request: { url: new URL(path, base).href, method, mode },
        respondWith(promise) { result = promise; }
      });
      return result;
    }
  };
}

test("install precaches every declared file under the hosting subdirectory", async () => {
  const w = worker();
  await w.lifecycle("install");
  assert.equal(w.requests.length, 30);
  assert(w.skipped);
  for (const request of w.requests) {
    assert(request.url.startsWith("https://example.test/seoik.com/"));
    assert.equal(request.cache, "reload");
  }
});

test("failed precaching rejects installation", async () => {
  const w = worker();
  w.setOffline(true);
  await assert.rejects(w.lifecycle("install"), /Offline/);
  assert.equal(w.skipped, false);
});

test("offline root and query navigation use the cached app shell", async () => {
  const w = worker();
  await w.lifecycle("install");
  w.setOffline(true);
  for (const path of ["./", "./?source=home", "index.html?source=home"]) {
    assert.equal(await (await w.request(path)).text(), "online");
  }
});

test("the Korean HTML entry point works offline", async () => {
  const w = worker();
  await w.lifecycle("install");
  w.setOffline(true);
  assert.equal(await (await w.request("서익닷컴.html")).text(), "online");
});

test("online navigation refreshes the document for the next offline launch", async () => {
  const w = worker();
  await w.lifecycle("install");
  w.setBody("updated");
  assert.equal(await (await w.request("./")).text(), "updated");
  w.setOffline(true);
  assert.equal(await (await w.request("./")).text(), "updated");
});

test("assets are available offline without a network fetch", async () => {
  const w = worker();
  await w.lifecycle("install");
  w.setOffline(true);
  const count = w.requests.length;
  assert.equal(await (await w.request("pwa.js", { mode: "cors" })).text(), "online");
  assert.equal(w.requests.length, count);
});

test("API responses, other origins, unknown routes and writes are not intercepted", () => {
  const w = worker();
  for (const path of ["api/profile", "missing-page", "https://firestore.googleapis.com/v1/users", "https://example.test/other/index.html"]) {
    assert.equal(w.request(path), undefined);
  }
  assert.equal(w.request("index.html", { method: "POST" }), undefined);
});

test("activation removes only old app caches and claims clients", async () => {
  const w = worker();
  await w.lifecycle("install");
  await w.caches.open("seoik-app-old");
  await w.caches.open("another-app");
  await w.lifecycle("activate");
  assert(w.stores.has("seoik-app-v47"));
  assert(w.stores.has("another-app"));
  assert(!w.stores.has("seoik-app-old"));
  assert(w.claimed);
});
