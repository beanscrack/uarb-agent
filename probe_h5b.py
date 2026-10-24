import sys
sys.path.insert(0, ".")
import json
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    rows = visible_rows(pg)
    print("rows:", len(rows), "last:", rows[-1]["doc"], rows[-1]["x"], rows[-1]["y"])
    for k in (8, 9, 4):
        c = rows[k]
        el = pg.evaluate("""({x,y}) => {
            const all = [...document.querySelectorAll('.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
            const hit = all.find(e => { const r = e.getBoundingClientRect(); return Math.abs(r.y + r.height/2 - y) < 6 && Math.abs(r.x + r.width/2 - x) < 80; });
            if (!hit) return 'no-el';
            const r = hit.getBoundingClientRect();
            return JSON.stringify({cx: r.x+r.width/2, cy: r.y+r.height/2, top: r.y, h: r.height});
        }""", {"x": c["x"], "y": c["y"]})
        print("row", c["doc"], "elhit:", el)
        d = json.loads(el) if el.startswith("{") else None
        if d:
            pg.mouse.click(d["cx"], d["cy"])
            try:
                pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
                print("  -> modal OK")
                pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=4000)
                pg.wait_for_timeout(1500)
            except Exception:
                print("  -> NO modal")
    b.close()
