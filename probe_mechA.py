"""Capture mechanism A: context.on('response') -> store body. One row."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, tab_pos  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/probeA"); out.mkdir(parents=True, exist_ok=True)
hits = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())

    def on_resp(r):
        if "/dl/" in r.url:
            try:
                body = r.body()
            except Exception as e:  # noqa: BLE001
                hits.append(("ERR", r.url, str(e)))
                return
            hits.append(("OK", r.url, len(body)))
            (out / f"A_{r.url.split('/dl/')[-1].split('?')[0]}").write_bytes(body)

    ctx.on("response", on_resp)
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    pos = tab_pos(pg, "Exhibits")
    for k in range(3):
        # first GO GET IT
        loc = pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first
        loc.click()
        pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        btn = pg.locator(".v-window .fm-download-button:not(.v-disabled)").first
        btn.click()
        t0 = time.time()
        while time.time() - t0 < 40 and not any(h[0] == "OK" for h in hits[k:]):
            pg.wait_for_timeout(200)
        print(f"cycle {k}: hits={ [(h[0], h[1][:70], h[2]) for h in hits] }")
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        pg.wait_for_timeout(1500)
    b.close()
