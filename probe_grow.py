"""Grow-the-list probing: read the grow window, click Go, track rows count, repeat."""
import sys, re
sys.path.insert(0, ".")
import time

from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter, visible_rows

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Other Documents", min_rows=6)

    def grow_state():
        return pg.evaluate("""() => {
            const w = [...document.querySelectorAll('.v-window')].find(x => /Grow the list/i.test(x.innerText||''));
            if (!w) return null;
            const m = w.innerText.match(/Grow the list\\.? \\((\\d+) of (\\d+)\\)/i);
            const go = [...w.querySelectorAll('.v-button')].find(x => /^\\s*Go\\s*$/i.test(x.innerText||''));
            const r = go ? go.getBoundingClientRect() : null;
            return JSON.stringify({cur: m?+m[1]:null, max: m?+m[2]:null, go: r?{x:r.x+r.width/2,y:r.y+r.height/2}:null});
        }""")

    def extra_rows():
        return pg.evaluate("""() => {
            const all = [...document.querySelectorAll('.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
            const ys = all.map(e => e.getBoundingClientRect().y).sort((a,b)=>a-b);
            return JSON.stringify({n: ys.length, y0: ys[0], y1: ys[1]||null, ymin: ys[0], ymax: ys.at(-1)});
        }""")

    rows = visible_rows(pg)
    print("start rows:", len(rows), extra_rows())
    for k in range(25):
        gs = grow_state()
        print(g" " if False else gs)
        if not gs:
            print(f"grow at {k}")
            break
        d = __import__("json").loads(gs)
        print(f"  grow: {d['cur']} of {d['max']}")
        if d["cur"] >= d["max"]:
            break
        pg.mouse.click(d["go"]["x"], d["go"]["y"])
        pg.wait_for_timeout(2500)
        # settle any confirm
        pg.evaluate("""() => { const w=[...document.querySelectorAll('.v-window')].find(x=>/are you sure|Want to grow/i.test(x.innerText||'')); if(w){const b=w.querySelector('.v-button-primary'); b&&b.click();} }""")
        pg.wait_for_timeout(1800)
        print("   ->", extra_rows(), "walker:", len(visible_rows(pg)))
        rows = visible_rows(pg)
    print("final rows:", len(rows))
    b.close()
