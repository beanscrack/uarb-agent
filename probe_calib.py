"""Calibrate row extraction + portal paging on Exhibits for a matter (1 cycle)."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import BASE, TABS, open_tab, read_metadata, search_matter, tab_pos, visible_rows  # noqa: E402

matter = sys.argv[1] if len(sys.argv) > 1 else "M12205"
tab = sys.argv[2] if len(sys.argv) > 2 else "Exhibits"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, matter)
    meta = read_metadata(pg)
    print("counts:", meta["counts"])
    open_tab(pg, tab, min_rows=1)
    pgs = []
    seen_first = None
    page_no = 0
    for _ in range(12):
        rows = visible_rows(pg)
        pgs.append([r["doc"] for r in rows])
        if seen_first is None:
            seen_first = rows[0]["doc"] if rows else None
        pos = tab_pos(pg, tab)
        # click far-right portal arrow widget: use the last GO GET IT row bottom-right area
        # In probing: down-arrow click at (1248,321). Compute: last row y + ? -> click base right edge.
        pg.mouse.click(1248, pos["y"] + 40)
        pg.wait_for_timeout(2500)
        page_no += 1
        first = (visible_rows(pg) or [{}])[0].get("doc")
        if seen_first is not None and first == seen_first and page_no > 0:
            break
    json.dump(pgs, open("calib_pages.json", "w"), indent=1)
    for i, g in enumerate(pgs):
        print(f"page{i}: n={len(g)}", g)
    b.close()
