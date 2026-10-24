"""Mechanism C: CDP Network.webSocketFrame* / Resource setContent? No — Mechanism C:
Patch window.open BEFORE the site GWT boots (context.add_init_script) so the download GET runs
in the MAIN page via a hidden <a download>/fetch trick? Simpler: the site itself uses
window.open; intercept window.open to route the URL through fetch() + store as
arraybuffer, expose on window for reading. Proven idea: page fetch of same-session URL works
(verified 200 + bytes). capture = window.open(url) -> we override window.open to also fetch().
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, visible_rows  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/mechC"); out.mkdir(parents=True, exist_ok=True)
INIT = """
window.__dl = {urls: [], chunks: {}};
const _open = window.open;
window.open = function (url, ...rest) {
  try {
    if (typeof url === 'string' && /\\/dl\\//.test(url)) {
      window.__dl.urls.push(url);
      fetch(url, {credentials: 'include'}).then(r => r.arrayBuffer().then(buf => {
        const bytes = new Uint8Array(buf);
        let bin = '';
        for (let i = 0; i < bytes.length; i += 8192) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192));
        window.__dl.chunks[url] = btoa(bin);
      }));
      return null;  // suppress the popup entirely
    }
  } catch (e) { window.__dl.urls.push('ERR ' + e); }
  return _open.call(window, url, ...rest);
};
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    ctx.add_init_script(INIT)
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    for k in range(13):
        pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        except Exception as e:  # noqa: BLE001
            print(f"cycle {k}: no modal -> {e}")
            break
        loc = pg.locator(".v-window .fm-download-button:not(.v-disabled)").first
        try:
            loc.wait_for(state="visible", timeout=15000)
            loc.click()
        except Exception as e:  # noqa: BLE001
            print(f"cycle {k}: no download button -> {e}")
            break
        t0 = time.time()
        while time.time() - t0 < 60:
            done = pg.evaluate("() => Object.keys(window.__dl.chunks).length")
            if done >= k + 1:
                break
            pg.wait_for_timeout(250)
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        pg.wait_for_timeout(1200)
        if (k + 1) % 4 == 0:
            print(f"cycle {k}: urls={pg.evaluate('window.__dl.urls')} chunks={pg.evaluate('Object.keys(window.__dl.chunks).length')}")
    # dump
    info = pg.evaluate("""() => JSON.stringify({urls: window.__dl.urls, keys: Object.keys(window.__dl.chunks).map(u => [u, window.__dl.chunks[u].length])})""")
    j = json.loads(info)
    print("urls:", j["urls"])
    for key, ln in j["keys"]:
        import base64

        data = base64.b64decode(pg.evaluate(f"window.__dl.chunks[{json.dumps(key)}]"))
        (out / key.split("/dl/")[-1].split("?")[0].replace("/", "_")).write_bytes(data)
        print("saved", key.split("/dl/")[-1], len(data))
    b.close()
