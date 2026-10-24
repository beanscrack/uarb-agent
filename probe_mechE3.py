import sys, time
sys.path.insert(0, ".")
from pathlib import Path
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

out = Path("C:/Users/fortn/task1/out_test/mechE2"); out.mkdir(parents=True, exist_ok=True)
cap: dict = {}
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    popups = []
    ctx.on("page", lambda pp: popups.append(pp))

    def handler(route):
        url = route.request.url
        if url in cap:
            route.continue_()
            return
        try:
            f = route.fetch(timeout=30000)
            body = f.body()
            cap[url] = (f.status, body)
            route.fulfill(status=f.status, body=body, headers={k: v for k, v in f.headers.items() if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception as e:
            cap[url] = ("ERR", str(e).encode())
            try:
                route.continue_()
            except Exception:
                pass

    ctx.route("**/dl/**", handler)
    search_matter(pg, "M12205")
    open_tab(pg, "Other Documents", min_rows=6)
    done: set[str] = set()
    okcnt = 0
    for k in range(16):
        rows = visible_rows(pg)
        cand = next((r for r in rows if r["doc"] not in done), None)
        if cand is None:
            print("no unseen rows", [r["doc"] for r in rows][:3])
            break
        pg.mouse.click(cand["x"], cand["y"])
        try:
            pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
        except Exception:
            print(f"c{k} doc={cand['doc']} NO MODAL")
            done.add(cand["doc"])
            continue
        en = pg.locator(".v-window .fm-download-button:not(.v-disabled)").count()
        if not en:
            print(f"c{k} doc={cand['doc']} NO BUTTON")
            done.add(cand["doc"])
            pg.keyboard.press("Escape")
            continue
        pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
        t0 = time.time()
        while time.time() - t0 < 40 and sum(1 for u in cap if cap[u][0] == 200) <= okcnt:
            pg.wait_for_timeout(250)
        for pp in popups:
            try:
                pp.close()
            except Exception:
                pass
        popups.clear()
        try:
            pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=5000)
        except Exception:
            pass
        pg.wait_for_timeout(2000)
        done.add(cand["doc"])
        okcnt += 1
        print(f"c{k} doc={cand['doc']} OK urls={len(cap)} bytes_ok={sum(1 for u in cap if cap[u][0]==200)}")
    print("captured:", [(u.split("/dl/")[-1], cap[u][0], len(cap[u][1])) for u in cap])
    for u, (s, d) in cap.items():
        if s == 200 and d.startswith(b"%PDF"):
            (out / u.split("/dl/")[-1]).write_bytes(d)
    b.close()
