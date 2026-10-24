"""Is row-9 dead in a session that harvested MECHANIC-E-STYLE vs the FULL scraper?
Differences probed: (a) popups closed each cycle, (b) not closing (hide), (c) wheel.
Each runs mechE loop to 8, then clicks row 9 and reports modal/no-modal."""
import sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

MODE = sys.argv[1]  # plain | hide | watcher

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    popups = []
    ctx.on("page", lambda pp: popups.append(pp))
    cap: dict = {}

    def handler(route):
        url = route.request.url
        if url in cap:
            route.continue_()
            return
        try:
            f = route.fetch(timeout=30000)
            cap[url] = (f.status, f.body())
            route.fulfill(status=f.status, body=cap[url][1],
                          headers={k: v for k, v in f.headers.items()
                                   if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception:
            try:
                route.continue_()
            except Exception:
                pass

    ctx.route("**/dl/**", handler)
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    done: set = set()
    for k in range(8):
        rows = visible_rows(pg)
        cand = next((r for r in rows if r["doc"] not in done), None)
        if cand is None:
            break
        done.add(cand["doc"])
        pg.mouse.click(cand["x"], cand["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        except Exception:
            print("early no-modal at", k, cand["doc"])
            break
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 40 and not [u for u in cap if cap[u][0] == 200]:
            pg.wait_for_timeout(250)
        t0 = time.time()
        while time.time() - t0 < 15 and len(popups) < 1:
            pg.wait_for_timeout(200)
        if MODE == "plain":
            for pp in popups:
                try:
                    pp.close()
                except Exception:
                    pass
        popups.clear()
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:
            pg.keyboard.press("Escape")
        pg.wait_for_timeout(1800)
        print("cycle", k, cand["doc"], "ok", "popups_seen" if cap else "", flush=True)
    # now the row-9 test
    rows = visible_rows(pg)
    print("visible now:", [r["doc"] for r in rows])
    nxt = next((r for r in rows if r["doc"] not in done), None)
    if nxt:
        pg.mouse.click(nxt["x"], nxt["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
            print("ROW9 MODAL OK mode=", MODE)
        except Exception:
            w = pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' ')).join('//')")
            print("ROW9 NO MODAL mode=", MODE, "wins:", w[:120])
    b.close()
