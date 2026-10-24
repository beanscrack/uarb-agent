"""Why do rows 9+ die: probe the grid widget contract — virtual scroll? selection? arrows?"""
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
    # harvest 8 quickly
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
            print("early", k); break
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
    print("harvested", len(cap), flush=True)
    # inspect grid after wall
    probe = pg.evaluate("""() => {
        const els = [...document.querySelectorAll('[class*=grid], [class*=portal], [class*=scroll], [class*=list]')];
        const out = els.map(e => ({c: (e.className||'').toString().slice(0,60), sh: e.scrollHeight, ch: e.clientHeight, st: e.scrollTop}))
                       .filter(x => x.sh > x.ch + 5).slice(0, 8);
        const win = [...document.querySelectorAll('.v-window')].map(w => (w.innerText||'').replace(/\\n/g,' ').slice(0,60));
        return JSON.stringify({scrollers: out, wins: win, vals: [...document.querySelectorAll('input')].length}, null, 0);
    }""")
    print("probe:", probe[:600], flush=True)
    # grid keys: click row1, End key, wheel inside grid
    el = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||''));
        const b = all[0]; const r = b.getBoundingClientRect(); return JSON.stringify({x: r.x+r.width/2, y: r.y+r.height/2});
    }""")
    import json as J
    e = J.loads(el)
    pg.keyboard.press("End")
    pg.wait_for_timeout(1500)
    print("after End rows:", [r["doc"] for r in visible_rows(pg)][:4], flush=True)
    pg.mouse.click(600, 500)
    pg.keyboard.press("End")
    pg.wait_for_timeout(1500)
    rws = visible_rows(pg)
    print("after grid-click+End rows:", len(rws), rws[:2] and rws[8:], flush=True)
    b.close()
