"""When does the exhibits row box become complete? open tab -> poll visible_rows over time."""
import sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import _ROWS_JS, search_matter, tab_pos

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    pos = tab_pos(pg, "Exhibits")
    pg.mouse.click(pos["x"], pos["y"])
    for t in range(12):
        pg.wait_for_timeout(2000)
        n = len(pg.evaluate(_ROWS_JS))
        ggi = pg.evaluate("() => [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'')).length")
        print(f"t+{(t+1)*2}s rows_js={n} ggi={ggi}", flush=True)
        if n >= 6:
            break
    b.close()
