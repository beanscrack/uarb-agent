"""Where are per-matter FMIOMResRpc requests visible? context-wide request listener +
response listener, 30s window, log every fmi request URL + list response bodies."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, read_metadata, search_matter  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/rpclog"); out.mkdir(parents=True, exist_ok=True)
logf = (out / "log.txt").open("a", encoding="utf-8")
seen = set()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())

    def on_req(r):
        u = r.url
        if "/fmi/webd/" in u and u not in seen:
            seen.add(u)
            mt = (r.method, (r.post_data or "")[:120])
            logf.write(f"REQ {u}\n   {mt}\n")
            logf.flush()

    def on_resp(r):
        u = r.url
        if "FMIOMResRpc" in u:
            try:
                body = r.text()
            except Exception as e:  # noqa: BLE001
                body = f"ERR {e}"
            (out / f"resp_{len(seen)}.txt").write_text(body, encoding="utf-8", errors="replace")
            logf.write(f"RESP {u} len={len(body)}\n")
            logf.flush()

    ctx.on("request", on_req)
    ctx.on("response", on_resp)
    search_matter(pg, "M12205")
    meta = read_metadata(pg)
    open_tab(pg, "Exhibits", min_rows=6)
    # click row-1 GO GET IT (modal) and büyülü: capture all
    pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
    pg.wait_for_timeout(6000)
    print("logged", len(seen), "requests")
    b.close()
