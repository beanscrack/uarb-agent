"""Debug box walk for an Exhibits GO GET IT leaf."""
import json
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=6)
    dump = pg.evaluate("""() => {
        const gLeaves = [...document.querySelectorAll('div,span,button,a')]
            .filter(e => e.children.length === 0 && /GO GET IT/i.test(e.textContent || '') && (e.offsetWidth || e.offsetHeight));
        const g = gLeaves[2];
        const out = [];
        let box = g;
        for (let i = 0; i < 8 && box.parentElement; i++) {
            box = box.parentElement;
            const t = box.innerText || '';
            out.push({i, has: /GO GET IT/.test(t), pHas: box.parentElement ? /GO GET IT/.test(box.parentElement.innerText||'') : null, txt: t.replace(/\\n/g,'|').slice(0,80)});
        }
        return JSON.stringify(out, null, 0);
    }""")
    print(dump)
    b.close()
