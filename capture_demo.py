"""Capture live demo screenshots (headed browser) for the narrated demo video."""
import sys
sys.path.insert(0, ".")
from pathlib import Path

from playwright.sync_api import sync_playwright

import uarb_scrape as U

shots = Path("C:/Users/fortn/task1/uarb_agent/demo_src")
shots.mkdir(exist_ok=True)
n = [0]


def snap(pg, tag):
    n[0] += 1
    p = shots / f"{n[0]:02d}_{tag}"
    pg.screenshot(path=str(p))
    print("shot", p, flush=True)


with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto(U.BASE, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(7000)
    snap(pg, "search.png")
    U.type_text(pg, "#b0p0o254i0i0r1", "M12205")
    snap(pg, "typed.png")
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=40000)
    snap(pg, "result.png")
    U.open_tab(pg, "Exhibits", min_rows=6)
    snap(pg, "exhibits.png")
    rows = U.visible_rows(pg)
    c = rows[0]
    pg.mouse.click(c["x"], c["y"])
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=20000)
    snap(pg, "modal.png")
    b.close()
print("done")
