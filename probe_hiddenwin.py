"""Row 9 dead. Dump EVERY .v-window container class, all .v-window-wrap/.v-vertically
centered hidden windows, computed styles of the modal ROOT, and GWT overlay layers."""
import json
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

    # harvest 8
    cap: dict = {}
    popups = []
    def h(route):
        u = route.request.url
        if u not in cap:
            cap[u] = 1
            r = route.fetch(timeout=30000)
            route.fulfill(status=r.status, body=r.body(),
                          headers={k: v for k, v in r.headers.items()
                                   if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        else:
            route.continue_()
    pg.context.route("**/dl/**", h)
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
            print("EARLY WALL", k, cand["doc"], flush=True)
            break
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        import time
        t0 = time.time()
        while time.time() - t0 < 40 and len(cap) <= k:
            pg.wait_for_timeout(250)
        for pp in popups:
            try:
                pp.close()
            except Exception:
                pass
        popups.clear()
        for _ in range(3):
            try:
                pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
                break
            except Exception:
                pg.keyboard.press("Escape")
                pg.wait_for_timeout(800)
        pg.wait_for_timeout(1500)
    print("harvested", len(cap), flush=True)

    # click row 9 (dead) then dump EVERY window object + portal internals
    rows = visible_rows(pg)
    n9 = next((r for r in rows if r["doc"] not in done), None)
    pg.mouse.click(n9["x"], n9["y"])
    import time as _t
    _t.sleep(8)
    tabs = pg.evaluate("[...document.querySelectorAll('button.fm-widget')].map(b=>(b.textContent||'').trim().slice(0,18)).filter(t=>t)")
    print("tabs after dead click:", tabs[:12], flush=True)
    dump = pg.evaluate("""() => {
        const wins = [...document.querySelectorAll('.v-window')].map(w => ({
            cls: (w.className||'').slice(0,80), txt: (w.innerText||'').replace(/\\n/g,' ').slice(0,40),
            vis: !!(w.offsetWidth||w.offsetHeight), style: (w.getAttribute('style')||'').slice(0,80)}));
        const wraps = [...document.querySelectorAll('.v-window-wrap')].map(w => ({cls: (w.className||'').slice(0,50), vis: !!(w.offsetWidth||w.offsetHeight), style: (w.getAttribute('style')||'').slice(0,80)}));
        const layers = [...document.querySelectorAll('body > div')].map(d => ({cls: (d.className||'').slice(0,50)}));
        return JSON.stringify({wins, wraps, layers});
    }""")
    d = json.loads(dump)
    print("WINS:", json.dumps(d["wins"], indent=1)[:900], flush=True)
    print("WRAPS:", json.dumps(d["wraps"], indent=1)[:700], flush=True)
    print("BODY>LAYERS:", json.dumps(d["layers"], indent=1)[:700], flush=True)
    b.close()
