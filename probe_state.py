"""Run scrape with screenshots on cycle failure (headful-free) for M12205/Other Documents,
first 6 rows, with per-cycle state dumps."""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import (  # noqa: E402
    harvest_one_row,
    norm_doc_type,
    open_tab,
    read_metadata,
    search_matter,
    visible_rows,
)

matter, doc_type = "M12205", norm_doc_type("Other Documents")
out = Path("C:/Users/fortn/task1/out_test/probeState"); out.mkdir(parents=True, exist_ok=True)
names: set[str] = set()
done: set[str] = set()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, matter)
    meta = read_metadata(pg)
    open_tab(pg, doc_type, min_rows=6)
    fc = pg.evaluate("() => (document.body.innerText.match(/Found Count: \\\\d+/)||['?'])[0]")
    print(fc)
    for k in range(8):
        rows = visible_rows(pg)
        cand = next((r for r in rows if r["doc"] not in done), None)
        print(f"--- cycle {k}: rows={[r['doc'] for r in rows]} cand={cand['doc'] if cand else None}")
        if cand is None:
            break
        try:
            rec = harvest_one_row(pg, cand, out, names)
            done.add(cand["doc"])
            print(f"   OK {rec['name'] if rec else 'dup'}")
        except Exception as e:  # noqa: BLE001
            pg.screenshot(path=str(out / f"fail_{k}_{cand['doc']}.png"))
            txt = pg.evaluate("[...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' | ')).join(' /// ')")
            print(f"   FAIL {type(e).__name__}: {str(e)[:120]}")
            print(f"   windows: {txt[:200]}")
            b.close()
            sys.exit(1)
    b.close()
