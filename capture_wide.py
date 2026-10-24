"""Capture ONE ruled (red-border, wide) video per tab for the demo: Rules box +
tab rentals + portal content, Key Documents + Other Documents."""
import sys
sys.path.insert(0, ".")
from pathlib import Path

from playwright.sync_api import sync_playwright

import uarb_scrape as U

shots = Path("C:/Users/fortn/task1/uarb_agent/demo_src")
shots.mkdir(exist_ok=True)


def snap(pg, tag):
    p = shots / tag
    pg.screenshot(path=str(p), full_page=True)
    print("shot", p, flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    pg = b.new_page(viewport={"width": 1600, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto(U.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(7000)
    U.type_text(pg, "#b0p0o254i0i0r1", "M12205")
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=40000)
    pg.wait_for_timeout(1200)
    snap(pg, "wide_result.png")
    for tab, tag in [("Key Documents", "wide_keydocs"), ("Other Documents", "wide_otherdocs")]:
        pos = U.tab_pos(pg, tab)
        pg.mouse.click(pos["x"], pos["y"])
        pg.wait_for_function(f"() => /{tab} - \\d+/.test(document.body.innerText)", timeout=60000)
        pg.wait_for_timeout(2500)
        snap(pg, f"{tag}.png")
    # zoom the rows on one tab (rows near the click point)
    pos = U.tab_pos(pg, "Other Documents")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_timeout(2500)
    rows = U.visible_rows(pg)
    # region crop centered on row list
    x0 = max(0, rows[0]["x"] - 560)
    y0 = max(0, rows[0]["y"] - 80)
    pg.screenshot(path=str(shots / "zoom_rows.png"), clip={"x": x0, "y": y0, "width": 1120, "height": min(880, 900 - y0)})
    print("shot zoom_rows", flush=True)
    b.close()
print("done")
