"""Isolate the 'Relationship Not Found' trigger: tall open -> click GO GET IT -> read window;
Close -> modal click -> read window (win+12s); row2/row3/row4 status."""
import sys
sys.path.insert(0, ".")
import json
import time
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 4200})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Other Documents", min_rows=40)
    rows = visible_rows(pg)
    print("rows:", len(rows))
    wins = lambda: pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
    for k in (0, 1, 2):
        c = rows[k]
        pg.mouse.click(c["x"], c["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
            modal = True
        except Exception:
            modal = False
        print(f"row{k} doc={c['doc']} modal={modal} wins: {wins()[:150]}")
        if modal:
            btn = pg.locator(".v-window .fm-download-button:not(.v-disabled)")
            n = btn.count()
            print(f"  dl enabled={n}")
            if n:
                btn.first.click()
                time.sleep(12)
                print(f"  after modal click wins: {wins()[:120]}")
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=6000)
            pg.wait_for_timeout(1500)
    b.close()
