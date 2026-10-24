import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    rows = visible_rows(pg)
    print("rows:", len(rows), [r["doc"] for r in rows])
    if rows:
        c = rows[0]
        pg.mouse.click(c["x"], c["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
            en = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
            print("modal OK enabled=", en)
        except Exception:
            wins = pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
            print("NO MODAL |", wins[:120])
    b.close()
