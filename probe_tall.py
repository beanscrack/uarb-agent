import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, read_metadata, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 4200})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    meta = read_metadata(pg)
    open_tab(pg, "Other Documents", min_rows=40)
    rows = visible_rows(pg)
    print("rows:", len(rows), [r["doc"] for r in rows])
    b.close()
