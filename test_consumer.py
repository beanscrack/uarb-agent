"""Definitive consumer test: harvest N=./n_target rows from a tab in ONE run:
rows -> (doc==filename) -> sequential GO GET IT cycles -> Save List early-exit."""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import (  # noqa: E402
    harvest_one_row,
    is_gone,
    norm_doc_type,
    open_tab,
    read_metadata,
    search_matter,
    visible_rows,
)

matter = sys.argv[1]
doc_type = norm_doc_type(sys.argv[2])
n_target = int(sys.argv[3]) if len(sys.argv) > 3 else 999
out_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("C:/Users/fortn/task1/out_test")
out_dir.mkdir(parents=True, exist_ok=True)
names: set[str] = set()

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, matter)
    meta = read_metadata(pg)
    n_target = min(n_target, meta["counts"].get(doc_type) or 0)
    print("target:", n_target)
    open_tab(pg, doc_type, min_rows=min(n_target, 6))
    harvested = []
    guard = 0
    stall = 0
    page_snap: tuple = ()
    # FileMaker portal rows visible are the FIRST N (no paging: growing restarts, wheel &
    # arrows no-op). If 'Save List' export works, expect the file list == names we harvest.
    for guard in range(n_target + 8):
        rows = visible_rows(pg)
        cand = next((r for r in rows if r["doc"] and r["doc"] not in {h["doc"] for h in harvested}), None)
        if cand is None:
            snap = tuple(sorted(r["doc"] for r in rows))
            if snap == page_snap:
                stall += 1
            page_snap = snap
            if stall >= 2:
                print("stalled visible set:", snap)
                break
            pg.mouse.wheel(0, 500)
            pg.wait_for_timeout(1500)
            continue
        stall = 0
        try:
            rec = harvest_one_row(pg, cand, out_dir, names)
            if is_gone(pg, cand["doc"]):
                print(f"row doc={cand['doc']} -> FILE GONE on server (skipped)")
                if rec is None:
                    # consume it as visited (the doc is gone; nothing to harvest)
                    harvested.append({"doc": cand["doc"], "gone": True})
                    continue
            if rec:
                rec["gone"] = False
                harvested.append(rec)
                print(f"[{len(harvested)}/{n_target}] row={cand['doc']} -> {rec['name']} ({rec['bytes']} b)")
            else:
                print(f"row={cand['doc']} -> dup {cand['doc']}")
                harvested.append({"doc": cand["doc"], "dup": True})
        except Exception as e:  # noqa: BLE001
            print(f"row={cand['doc']} ERROR {e}")
            (out_dir / "errors.log").open("a").write(f"{cand['doc']}: {e}\n")
            pg.keyboard.press("Escape")
            pg.wait_for_timeout(1000)
        if len([h for h in harvested if not h.get("gone")]) >= n_target:
            break
    print("done:", len([h for h in harvested if not h.get('gone')]), "files,", "gone:", [h["doc"] for h in harvested if h.get("gone")], "dup:", [h["doc"] for h in harvested if h.get("dup")], "guard:", guard)
    b.close()
