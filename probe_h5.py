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
    wins = lambda: pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
    rows = visible_rows(pg)
    print("rows:", [r["doc"] for r in rows])
    c = rows[8] if len(rows) > 8 else rows[-1]
    print("click", c["doc"])
    pg.mouse.click(c["x"], c["y"])
    import time
    for t in (3, 8, 14):
        time.sleep(t if t == 3 else 5)
        print(f"t~{t}s wins:", wins()[:200])
    b.close()
