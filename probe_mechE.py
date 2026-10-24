"""Mechanism E: passthrough route with SEMANTIC HARVESTING: click the FIRST unseen doc's GO
GET IT; route stores (url, body). Integrity: each cycle must serve a NEW doc (urls distinct);
after all, row set intact?"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, visible_rows  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/mechE"); out.mkdir(parents=True, exist_ok=True)
cap: dict = {}

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    popups = []
    ctx.on("page", lambda p2: popups.append(p2))

    def handler(route):
        url = route.request.url
        if url in cap:
            route.continue_()  # passthrough
            return
        try:
            fetch = route.fetch(timeout=20000)
            body = fetch.body()
            cap[url] = (fetch.status, body)
            route.fulfill(status=fetch.status, body=body, headers={k: v for k, v in fetch.headers.items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception as e:  # noqa: BLE001
            cap[url] = ("ERR", str(e).encode())
            try:
                route.continue_()
            except Exception:  # noqa: BLE001
                pass

    ctx.route("**/dl/**", handler)
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    done: set[str] = set()
    for k in range(4):
        rows = visible_rows(pg)
        cand = next((r for r in rows if r["doc"] not in done), None)
        if cand is None:
            print("no unseen rows:", [r["doc"] for r in rows])
            break
        pg.mouse.click(cand["x"], cand["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        except Exception:
            print(f"cycle {k}: NO MODAL for doc={cand['doc']}")
            break
        enabled = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
        print(f"cycle {k}: doc={cand['doc']} modal enabled={enabled}")
        if not enabled:
            break
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 45 and len(cap) <= k:
            pg.wait_for_timeout(250)
        for pp in popups:
            try:
                pp.close()
            except Exception:  # noqa: BLE001
                pass
        popups.clear()
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:  # noqa: BLE001
            pass
        pg.wait_for_timeout(1500)
        done.add(cand["doc"])
    print("captured:", [(u.split('/dl/')[-1], cap[u][0], len(cap[u][1])) for u in cap])
    for u, (st, body) in cap.items():
        if isinstance(body, bytes) and st == 200 and body.startswith(b"%PDF"):
            (out / u.split("/dl/")[-1]).write_bytes(body)
    rows = visible_rows(pg)
    print("final rows:", [r["doc"] for r in rows])
    # cycle5 after 4 cycles: row[0] (the NOT-done first) modal:
    cand = next((r for r in rows if r["doc"] not in done), None)
    if cand:
        pg.mouse.click(cand["x"], cand["y"])
        pg.wait_for_timeout(2500)
        enabled = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
        modal = pg.locator(".v-window:has-text('Download Files')").count()
        allwin = pg.evaluate("() => [...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
        print(f"cycle5 doc={cand['doc']} modal={modal} enabled={enabled} text={allwin[:150]}")
    b.close()
