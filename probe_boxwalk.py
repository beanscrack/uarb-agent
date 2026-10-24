"""Why do Exhibits rows return []? Dump the evaluate result for box walk (fixed)."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

JS = """() => {
    const gLeaves = [...document.querySelectorAll('div,span,button,a')]
        .filter(e => e.children.length === 0 && /GO GET IT/i.test(e.textContent || '') && (e.offsetWidth || e.offsetHeight));
    const boxes = new Map();
    for (const g of gLeaves) {
        let box = g, path = [];
        for (let i = 0; i < 12 && box.parentElement; i++) {
            box = box.parentElement;
            const parHas = box.parentElement ? /GO GET IT/.test(box.parentElement.innerText || '') : true;
            path.push({i, parHas});
            if (i >= 5 && !parHas) break;
        }
        if (!boxes.has(box)) boxes.set(box, {g, path});
    }
    return JSON.stringify([...boxes.values()].map(o => {
        const texts = []; (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) texts.push(t);} else for(const c of n.childNodes) w(c); })(/*box*/ null || o.box || (function(){ const nodes=[...boxes.keys()]; const idx=nodes.findIndex(n=>n===o.g); return nodes[idx]; })());
        return {texts, path: o.path};
    }));
}"""

# simpler: evaluate then map
JS2 = """() => {
    const gLeaves = [...document.querySelectorAll('div,span,button,a')]
        .filter(e => e.children.length === 0 && /GO GET IT/i.test(e.textContent || '') && (e.offsetWidth || e.offsetHeight));
    const rows = [];
    for (const g of gLeaves) {
        let box = g;
        for (let i = 0; i < 12 && box.parentElement; i++) {
            box = box.parentElement;
            const parHas = box.parentElement ? /GO GET IT/.test(box.parentElement.innerText || '') : true;
            if (i >= 5 && !parHas) break;
        }
        const texts = []; (function w(n){ if(n.nodeType===3){const t=n.nodeValue.trim(); if(t) texts.push(t);} else for(const c of n.childNodes) w(c); })(box);
        rows.push(texts);
    }
    return JSON.stringify(rows);
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    out = json.loads(pg.evaluate(JS2))
    for t in out[:3]:
        print(len(t), t)
    b.close()
