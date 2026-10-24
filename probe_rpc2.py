"""Dump post-matter-search RPC calls (UIDL POST bodies) looking for the file list.
Click row1 GO GET IT + download button, log everything with bodies >2KB."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

out = Path("C:/Users/fortn/task1/out_test/rpc2"); out.mkdir(parents=True, exist_ok=True)
n = [0]

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())

    def on_req(r):
        u = r.url
        pd = r.post_data
        if u.endswith("/dl/"):
            return
        body = pd or ""
        if "/webd/UIDL" in u:
            # every RPC: dump each rpc call name
            import json as _j

            try:
                j = _j.loads(body)
                calls = [c[1] + ":" + c[2] for c in j.get("rpc", []) if isinstance(c, list) and len(c) >= 3]
                (out / "rpc_names.txt").open("a", encoding="utf-8").write(";".join(calls) + "\n")
            except Exception:  # noqa: BLE001
                pass
            if len(body) > 3000:
                n[0] += 1
                (out / f"uidl_{n[0]}.txt").write_text(body, encoding="utf-8", errors="replace")

    ctx.on("request", on_req)
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    pg.locator(".fm-widget.hand-cursor", has_text="GO GET IT").first.click()
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    pg.locator(".v-window .fm-download-button:not(.v-disabled)").first.click()
    pg.wait_for_timeout(5000)
    print("big uidl bodies:", n[0])
    b.close()
