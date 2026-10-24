import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

from uarb_scrape import open_tab, search_matter

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    probe = pg.evaluate("""() => {
        const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let tn = null;
        while (w.nextNode()) { if (/^\\.pdf$/.test((w.currentNode.nodeValue||'').trim())) { tn = w.currentNode; break; } }
        const chain = [];
        let box = tn.parentElement;
        for (let i = 0; i < 14 && box; i++) {
            const texts = [];
            (function walk(n) {
                if (n.nodeType === 3) { const t = n.nodeValue.trim(); if (t) texts.push(t); }
                else for (const c of n.childNodes) walk(c);
            })(box);
            chain.push({i, tag: box.tagName, cls: (box.className||'').slice(0,40), n: texts.length, hasGi: texts.some(t=>/GO GET IT/i.test(t)), last2: texts.slice(-2)});
            box = box.parentElement;
        }
        return JSON.stringify(chain, null, 1);
    }""")
    print(probe)
    b.close()
