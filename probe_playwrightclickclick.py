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
    print([r["doc"] for r in rows])
    a = rows[4]["doc"]
    print("before:", a in [x["doc"] for x in visible_rows(pg)], flush=True)
    pg.locator("button.fm-widget.hand-cursor", has_text="GO GET IT").nth(4).click()
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
    pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
    pg.wait_for_timeout(1500)
    print("after close, a in rows:", a in [x["doc"] for x in visible_rows(pg)], flush=True)
    print("docs now:", [x["doc"] for x in visible_rows(pg)][:8], flush=True)
    b.close()
