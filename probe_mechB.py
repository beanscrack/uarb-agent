"""Mechanism B: read response.body() IMMEDIATELY in the handler (before navigation completes)
3 cycles; then check modal on row 3. Also dump popup page count. Then verify portal integrity
by harvesting row 3 with the same mechanism."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, visible_rows  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/mechB"); out.mkdir(parents=True, exist_ok=True)
bodies: list = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())

    def on_resp(r):
        if "/dl/" in r.url:
            try:
                bodies.append((r.url, r.body()))
            except Exception as e:  # noqa: BLE001
                bodies.append((r.url, b""))

    ctx.on("response", on_resp)
    popups = []
    ctx.on("page", lambda p2: popups.append(p2))
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    for k in range(3):
        pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
        pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 40 and len(bodies) <= k:
            pg.wait_for_timeout(200)
        print(f"cycle {k}: bodies={[(u.split('/dl/')[-1], len(d)) for u, d in bodies]} popups={len(popups)}")
        for pp in popups:
            try:
                pp.close()
            except Exception:  # noqa: BLE001
                pass
        popups.clear()
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        pg.wait_for_timeout(1500)
    # integrity check: rows visible + cycle 4 should yield H-4
    rows = visible_rows(pg)
    print("rows now:", [r["doc"] for r in rows])
    pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
    ok = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
    print("cycle4 modal enabled:", ok)
    for i, (u, d) in enumerate(bodies):
        if d:
            (out / f"B_{i}_{u.split('/dl/')[-1].split('?')[0]}").write_bytes(d)
    b.close()
