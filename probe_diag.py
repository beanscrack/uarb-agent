import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import _ROWS_JS, open_tab, search_matter

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    rows = pg.evaluate(_ROWS_JS)
    print("rows_js:", rows)
    n = pg.evaluate("""() => {
        const all = [...document.querySelectorAll('.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        return JSON.stringify({n: all.length, leaf: all.filter(e=>e.childElementCount===0).length, tags: all.slice(0,3).map(e=>e.tagName+'/'+(e.className||'').slice(0,50))}); }""")
    print("buttons:", n)
    ext = pg.evaluate("""() => {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let c = 0; while (walker.nextNode()) { if (/^\\.[A-Za-z0-9]{2,5}$/.test((walker.currentNode.nodeValue||'').trim())) c++; }
        return c; }""")
    print("extnodes:", ext)
    b.close()
