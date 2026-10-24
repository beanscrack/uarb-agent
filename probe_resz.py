import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import dismiss_grow_dialogs, search_matter, tab_pos, visible_rows

tall = sys.argv[1] == "tall"
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    # open Other Documents in 900, grow to full
    pos = tab_pos(pg, "Other Documents")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_timeout(1500)
    for _ in range(40):
        if not dismiss_grow_dialogs(pg):
            break
        pg.wait_for_timeout(200)
    pg.wait_for_timeout(1500)
    if tall:
        pg.set_viewport_size({"width": 1440, "height": 4200})
        pg.wait_for_timeout(2000)
        # re-locate row coords from the DOM after resize
    rows = visible_rows(pg)
    print("viewport tall" if tall else "viewport 900", "rows:", len(rows), [r["doc"] for r in rows][:3])
    cand = rows[0]
    pg.mouse.click(cand["x"], cand["y"])
    try:
        pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
        print("MODAL OK")
        win = pg.locator(".v-window").first.inner_text().replace("\n", " | ")[:80]
        print("win:", win)
    except Exception:
        wins = pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
        print("NO MODAL; windows:", wins[:150])
    b.close()
