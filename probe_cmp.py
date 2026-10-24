import sys, json
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright
from uarb_scrape import _ROWS_JS, open_tab, search_matter

SCAN = r"""() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const extNodes = [];
    while (walker.nextNode()) {
        const t = (walker.currentNode.nodeValue||'').trim();
        if (/^\.[A-Za-z0-9]{2,5}$/.test(t)) extNodes.push(walker.currentNode);
    }
    const out = [];
    for (const tn of extNodes) {
        let box = tn.parentElement;
        for (let i = 0; i < 10 && box.parentElement; i++) {
            const texts = [];
            (function walk(n) {
                if (n.nodeType === 3) { const t = n.nodeValue.trim(); if (t) texts.push(t); }
                else for (const c of n.childNodes) walk(c);
            })(box);
            const gi = texts.findIndex(t => /GO GET IT/i.test(t));
            if (gi >= 0 && texts[texts.length - 1] === tn.nodeValue.trim() && gi === texts.length - 2) {
                out.push(texts);
                break;
            }
            box = box.parentElement;
        }
    }
    return JSON.stringify(out);
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    mine = json.loads(pg.evaluate(SCAN))
    js = pg.evaluate(_ROWS_JS)
    print("RAW rows:", len(mine), "via _ROWS_JS:", len(js))
    print("RAW first:", mine[0] if mine else None)
    print("JS first:", js[0] if js else None)
    b.close()
