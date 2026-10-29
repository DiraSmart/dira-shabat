/**
 * Dira Shabat Card loader.
 *
 * Injected into index.html via add_extra_js_url. The Home Assistant frontend
 * only tries to import a Lovelace resource once per page load; if that single
 * fetch fails (flaky mobile data) or 404s (dashboard opened while HA is still
 * starting up), the card stays broken until the page is reloaded.
 *
 * This loader imports the card and retries with backoff. Each retry uses a
 * fresh query string so the browser doesn't reuse the cached failure from the
 * module map / HTTP cache.
 */
(async () => {
  const TAG = "dira-shabat-card";
  const self = new URL(import.meta.url);
  const version = self.searchParams.get("v") || "";
  const card = new URL("dira-shabat-card.js", self);
  if (version) card.searchParams.set("v", version);

  // ~2 minutes total, matching the backend's Lovelace retry window.
  const delaysMs = [0, 2000, 5000, 10000, 20000, 30000, 60000];

  for (let i = 0; i < delaysMs.length; i++) {
    if (customElements.get(TAG)) return;
    if (delaysMs[i]) await new Promise((r) => setTimeout(r, delaysMs[i]));
    if (customElements.get(TAG)) return;

    const url = new URL(card);
    if (i > 0) url.searchParams.set("r", String(i));
    try {
      await import(url.href);
      return;
    } catch (err) {
      console.warn(`[dira-shabat] card load attempt ${i + 1} failed:`, err?.message || err);
    }
  }
  console.error("[dira-shabat] giving up loading the card; reload the page to retry");
})();
