"""Calib3: exhibits arrows — locate by DOM arrows(27px at gogetit x-126)+probe click y at tab y+25."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, tab_pos  # noqa: E402

def ggi(pg):
    v = pg.evaluate("""() => {
        const g = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        return JSON.stringify(g.map(el => {
            let p = el; for (let i=0;i<9;i++){ p = p.parentElement; if ((p.innerText||'').includes('GO GET IT') && (p.innerText||'').split('\\n').length > 3) break; }
            const texts = []; (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) texts.push(t);} else for(const c of n.childNodes) w(c); })(p);
            return {texts, y: Math.round(el.getBoundingClientRect().y)};
        }));
    }""")
    return json.loads(v)

# exhibits arrows live ~x 1284-1360, tab row
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=1)
    pos = tab_pos(pg, "Exhibits")
    first_y = ggi(pg)[0]["y"]
    print("tab:", pos, "first row y:", first_y)
    seq = []
    tried = []
    for dy in [25, 40, 60, 80, -20, -40]:
        x, y = 1248, pos["y"] + dy
        pg.mouse.click(x, y)
        pg.wait_for_timeout(2500)
        rows = ggi(pg)
        sig = [r["texts"][0] for r in rows]
        tried.append((dy, sig[:3]))
    for dy, sig in tried:
        print("click y tab+", dy, "->", sig)
    b.close()
