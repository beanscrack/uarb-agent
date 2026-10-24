"""Calib4: wheel paging test on Exhibits — does the virtual portal shift rows?"""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

def ggi(pg):
    v = pg.evaluate("""() => {
        const g = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        return JSON.stringify(g.map(el => {
            let p = el; for (let i=0;i<9;i++){ p = p.parentElement; if ((p.innerText||'').includes('GO GET IT') && (p.innerText||'').split('\\n').length > 3) break; }
            const texts = []; (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) texts.push(t);} else for(const c of n.childNodes) w(c); })(p);
            const r = el.getBoundingClientRect();
            return {texts: texts.slice(0,6), y: Math.round(r.y)};
        }));
    }""")
    return json.loads(v)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=1)
    print("before:", [r["texts"][3] if len(r["texts"])>3 else r["texts"][0] for r in ggi(pg)])
    for dy in (30, 200, 500, 1500):
        pg.mouse.wheel(0, dy)
        pg.wait_for_timeout(1500)
        rows = ggi(pg)
        sig = [r["texts"][3] if len(r["texts"])>3 else r["texts"][0] for r in rows]
        ys = [r["y"] for r in rows]
        print(f"wheel {dy}: n={len(rows)} ymin={ys[0] if ys else '-'}", sig)
    b.close()
