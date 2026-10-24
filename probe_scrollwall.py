"""In-row9-dead state: scroll the grid body (wheel over grid + scrollTop), print GGI ys."""
import sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)

    def ggis():
        return pg.evaluate("""() => {
            const all = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||''));
            return JSON.stringify(all.map(e => Math.round(e.getBoundingClientRect().y)));
        }""")

    print("GGI ys init:", ggis(), flush=True)
    # harvest 8 via mechE
    cap: dict = {}
    def handler(route):
        url = route.request.url
        if url in cap:
            route.continue_()
            return
        try:
            f = route.fetch(timeout=30000)
            cap[url] = f.status
            route.fulfill(status=f.status, body=f.body(),
                          headers={k: v for k, v in f.headers.items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception:
            try:
                route.continue_()
            except Exception:
                pass
    pg.context.route("**/dl/**", handler)
    popups = []
    pg.context.on("page", lambda pp: popups.append(pp))
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
            print("early wall at", k, cand["doc"], flush=True)
            break
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 40 and sum(1 for v in cap.values() if v == 200) <= k:
            pg.wait_for_timeout(250)
        for pp in popups:
            try:
                pp.close()
            except Exception:
                pass
        popups.clear()
        pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        pg.wait_for_timeout(1500)
    print("harvested", len(cap), "GGI ys:", ggis(), flush=True)
    # row 9 dead click
    rows = visible_rows(pg)
    n9 = next((r for r in rows if r["doc"] not in done), None)
    pg.mouse.click(n9["x"], n9["y"])
    try:
        pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
        print("row9 modal!?")
    except Exception:
        print("row9 dead. windows:", pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' ').slice(0,50))"), flush=True)
    # now SCROLL the grid body by 360 and look
    pg.evaluate("""() => {
        for (const el of document.querySelectorAll('.v-grid-tablewrapper, .v-grid-scroller-vertical, .v-grid-body, .v-grid')) {
            el.scrollTop = 360;
        }
    }""")
    pg.wait_for_timeout(1800)
    print("GGI ys after scrollTop:", ggis(), flush=True)
    pg.mouse.wheel(0, 500)
    pg.wait_for_timeout(1800)
    print("GGI ys after wheel:", ggis(), flush=True)
    print("rows now:", [(r["doc"], r["y"]) for r in visible_rows(pg)], flush=True)
    g = next((r for r in visible_rows(pg) if r["doc"] not in done), None)
    if g:
        pg.mouse.click(g["x"], g["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=12000)
            en = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
            print("POST-SCROLL CLICK MODAL OK enabled=", en)
        except Exception:
            print("POST-SCROLL CLICK DEAD")
    b.close()
