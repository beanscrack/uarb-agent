"""Mechanism D: allowed context route with passthrough: route.fetch({max_redirects:0}) WITHOUT
abort (continue passthrough). Then check FileMaker stability across 3 downloads + row 4 modal."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, visible_rows  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/mechD"); out.mkdir(parents=True, exist_ok=True)
files: list = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    popups = []
    ctx.on("page", lambda p2: popups.append(p2))

    def handler(route):
        url = route.request.url
        try:
            fetch = route.fetch(max_redirects=0, timeout=20000)
            status = fetch.status
            if status in (302, 301, 303):
                loc = fetch.headers.get("location", "")
                files.append((url, "302->" + loc, 0, None, dict(fetch.headers)))
                route.fulfill(status=status, headers={"Location": loc})
                return
            body = fetch.body()
            files.append((url, status, len(body), body, dict(fetch.headers)))
            route.fulfill(status=status, body=body, headers={k: v for k, v in fetch.headers.items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception as e:  # noqa: BLE001
            files.append((url, "ERR", 0, None, str(e)))
            try:
                route.continue_()
            except Exception:  # noqa: BLE001
                pass

    ctx.route("**/dl/**", handler)
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    for k in range(3):
        pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
        pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 45 and len(files) <= k:
            pg.wait_for_timeout(250)
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
        print(f"cycle {k}:", [(f[1], f[2], f[0].split('/dl/')[-1]) for f in files])
    rows = visible_rows(pg)
    print("rows:", [r["doc"] for r in rows])
    pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
    pg.wait_for_timeout(2000)
    enabled = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
    modal = pg.locator(".v-window:has-text('Download Files')").count()
    txt = pg.evaluate("() => [...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
    print("c4 modal:", modal, "enabled:", enabled, "win text:", txt[:160])
    for i, f in enumerate(files):
        if f[3]:
            (out / f"D_{i}_{f[0].split('/dl/')[-1]}").write_bytes(f[3])
    b.close()
