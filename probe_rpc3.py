"""Log UIDL RPC POST bodies during the harvest cycles; look for the record organizes."""
import sys
sys.path.insert(0, ".")
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

out = Path("C:/Users/fortn/task1/out_test/rpc3"); out.mkdir(parents=True, exist_ok=True)
n = [0]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 4200})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())

    def on_req(r):
        if "/webd/" in r.url and r.method == "POST":
            pd = r.post_data or ""
            if len(pd) > 40:
                n[0] += 1
                (out / f"post_{n[0]:03d}.txt").write_text(pd, encoding="utf-8", errors="replace")

    ctx.on("request", on_req)
    search_matter(pg, "M12205")
    open_tab(pg, "Other Documents", min_rows=40)
    rows = visible_rows(pg)
    wins = lambda: pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
    for k in (0, 1, 2, 3):
        c = rows[k]
        pg.mouse.click(c["x"], c["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
        except Exception:
            t = wins()
            print(f"row{k} doc={c['doc']} NO MODAL wins: {t[:120]}")
            if k >= 2:
                break
            pg.evaluate("() => { const w=[...document.querySelectorAll('.v-window')].find(w=>/OK/.test(w.innerText)); if(w){const b=w.querySelector('.v-button-primary'); b&&b.click();} }")
            pg.wait_for_timeout(1200)
            continue
        btn = pg.locator(".v-window .fm-download-button:not(.v-disabled)")
        if btn.count():
            btn.first.click()
            time.sleep(8)
        pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=6000)
        pg.wait_for_timeout(3000)
        print(f"row{k} doc={c['doc']} ok wins: {wins()[:60]}")
    print("posts:", n[0])
    b.close()
