"""Portal paging calibration v2: arrows at TAB-Y+25, detect page loop via y-min. Also dump
a full 'Other Documents' row DOM to find the fields above the type (doc number)."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, read_metadata, search_matter, tab_pos, visible_rows  # noqa: E402

def ggi_info(pg):
    return pg.evaluate("""() => {
        const g = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        return JSON.stringify(g.map(el => {
            let row = el; for (let i=0;i<9;i++){ row = row.parentElement; if ((row.innerText||'').includes('GO GET IT') && (row.innerText||'').split('\\n').length > 3) break; }
            const texts = []; (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) texts.push(t);} else for(const c of n.childNodes) w(c); })(row);
            const r = el.getBoundingClientRect();
            return {texts, y: Math.round(r.y)};
        }));
    }""")

CLICK_Y_OFF = 25
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=1)
    pos = tab_pos(pg, "Exhibits")
    seen = []
    allinfo = []
    for pageno in range(6):
        info = json.loads(ggi_info(pg))
        allinfo.append(info)
        ymins = 10**9
        first = info[0]["texts"][0] if info else None
        seen.append(first)
        if pageno > 0 and first == seen[0]:
            break
        pg.mouse.click(1248, pos["y"] + CLICK_Y_OFF)
        pg.wait_for_timeout(2500)
    for i, info in enumerate(allinfo):
        print(f"page{i} n={len(info)} first={info[0]['texts'][:8] if info else None}")
    # dump Other Documents row0 structure
    open_tab(pg, "Other Documents", min_rows=1)
    dump = pg.evaluate("""() => {
        const g = [...document.querySelectorAll('button.fm-widget.hand-cursor')].find(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        let row = g;
        for (let i=0;i<12;i++){ row = row.parentElement; if ((row.innerText||'').includes('GO GET IT') && /Public|Confidential/.test(row.innerText||'')) break; }
        const leaves = [];
        (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) leaves.push(t);} else { for(const c of n.childNodes) w(c); } })(row);
        const attrs = [...row.querySelectorAll('[help],[title],img,[src]')].map(e => ({tag: e.tagName, help: e.getAttribute('help'), title: e.getAttribute('title'), src: (e.getAttribute('src')||'').slice(0,60), alt: e.getAttribute('alt')})).slice(0,12);
        return JSON.stringify({outer: row.outerHTML.slice(0, 2500), leaves, attrs}, null, 1);
    }""")
    print(dump)
    b.close()
