"""Census: how many row boxes does the walker find per tab? Prints texts of every box."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

WALK = """() => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const extNodes = [];
    while (walker.nextNode()) {
        const t = walker.currentNode.nodeValue.trim();
        if (/^\\.[A-Za-z0-9]{2,5}$/.test(t)) extNodes.push(walker.currentNode);
    }
    const boxes = [];
    for (const tn of extNodes) {
        let box = tn.parentElement, found = false, texts = null;
        for (let i = 0; i < 10 && box.parentElement; i++) {
            box = box.parentElement;
            const tt = [];
            (function w(n) {
                if (n.nodeType === 3) { const t = n.nodeValue.trim(); if (t) tt.push(t); }
                else for (const c of n.childNodes) w(c);
            })(box);
            const gi = tt.findIndex(t => /GO GET IT/i.test(t));
            if (gi >= 0 && tt[tt.length - 1] === tn.nodeValue.trim() && gi === tt.length - 2) {
                found = true; texts = tt; break;
            }
        }
        boxes.push({ext: tn.nodeValue.trim(), found, texts});
    }
    return JSON.stringify(boxes.map(b => [b.ext, b.found, (b.texts||[]).slice(0,8)]));
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    for tab in sys.argv[1:] or ["Exhibits", "Other Documents"]:
        open_tab(pg, tab, min_rows=6)
        boxes = json.loads(pg.evaluate(WALK))
        nf = [x for x in boxes if x[1]]
        print(tab, "boxes:", len(boxes), "matched:", len(nf))
        for x in boxes[:3]:
            print("  ", x)
    b.close()
