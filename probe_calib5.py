"""Calib v5 (definitive): exhibits list, click tab seg -> enter -> PageDown x2, dump rows at
each step with a CORRECT row-box walk (stop at the container whose texts include infobox)."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter, tab_pos  # noqa: E402

ROWS_JS = """() => {
    const gLeaves = [...document.querySelectorAll('div,span,button,a')]
        .filter(e => e.children.length === 0 && /GO GET IT/i.test(e.textContent || '') && (e.offsetWidth || e.offsetHeight));
    const boxes = new Map();
    for (const g of gLeaves) {
        let box = g;
        for (let i = 0; i < 12 && box.parentElement; i++) {
            box = box.parentElement;
            const t = box.innerText || '';
            if (i >= 5 && /GO GET IT/i.test(t) && !(box.parentElement && /GO GET IT/i.test(box.parentElement.innerText || ''))) break;
        }
        if (!boxes.has(box)) boxes.set(box, g);
    }
    const out = [];
    for (const [box, g] of boxes) {
        const texts = [];
        (function w(n) {
            if (n.nodeType === 3) { const t = n.nodeValue.trim(); if (t) texts.push(t); }
            else for (const c of n.childNodes) w(c);
        })(box);
        const r = g.getBoundingClientRect();
        out.push({texts, y: Math.round(r.y)});
    }
    out.sort((a, b) => a.y - b.y);
    return JSON.stringify(out.map(o => ({doc: o.texts.find(t => /^[A-Za-z]-\\d/.test(t)) || o.texts[0], n: o.texts.length, y: o.y})));
}"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    print("initial:", json.loads(pg.evaluate(ROWS_JS)))
    pos = tab_pos(pg, "Exhibits")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_timeout(900)
    print("after click-tabseg:", json.loads(pg.evaluate(ROWS_JS)))
    pg.keyboard.press("Enter")
    pg.wait_for_timeout(1200)
    print("after Enter:", json.loads(pg.evaluate(ROWS_JS)))
    for i in range(3):
        pg.keyboard.press("PageDown")
        pg.wait_for_timeout(1800)
        print(f"after PageDown #{i+1}:", json.loads(pg.evaluate(ROWS_JS)))
    b.close()
