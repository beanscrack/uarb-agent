"""Any use of rich row 'H-5'* freeze the portal to 8? (NO harvest, clicks-with-cancel)."""
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
    print("rows:", len(visible_rows(pg)), flush=True)
    for tgt in ("H-5(C)-ii", "H-5-iii", "H-6", "H-7"):
        # click row, cancel modal
        row = next((r for r in visible_rows(pg) if r["doc"] == tgt), None)
        print("row", tgt, "found:", bool(row), flush=True)
        if row is None:
            continue
        pg.mouse.click(row["x"], row["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=10000)
            print(" modal-open", flush=True)
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:
            print(" NO-modal", flush=True)
            b.close()
            break
        pg.wait_for_timeout(1500)
        print("after close", tgt, "rows:", len(visible_rows(pg)), flush=True)
    n = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||''));
        return JSON.stringify(all.map(e => Math.round(e.getBoundingClientRect().y))); }""")
    print("GGI ys:", n, flush=True)
    print("WIN TEXT:", pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' ').slice(0,60))"), flush=True)
    b.close()
