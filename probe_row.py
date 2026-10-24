"""Dump GO GET IT row structure on the Exhibits tab (labels, help attrs, row text)."""
import sys
import json
from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")
from uarb_scrape import open_tab, search_matter  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    search_matter(pg, "M12205")
    open_tab(pg, "Exhibits", min_rows=1)
    info = pg.evaluate("""() => {
        const gLeaves = [...document.querySelectorAll('div,span,button,a')]
            .filter(e => e.children.length === 0 && /GO GET IT/i.test(e.textContent || '') && (e.offsetWidth || e.offsetHeight));
        const rows = [];
        for (const g of gLeaves.slice(0, 3)) {
            let p = g.parentElement, row = null, chain = [];
            for (let i = 0; i < 9 && p; i++) {
                chain.push({i, tag: p.tagName, cls: (p.className||'').toString().slice(0,60), txt: (p.innerText||'').replace(/\\n/g,'|').slice(0,90)});
                const t = (p.innerText || '');
                if (/GO GET IT/i.test(t) && (p.innerText.split('\\n').filter(s=>s.trim()).length||0) <= 40) row = p;
                p = p.parentElement;
            }
            const help = [...(row||document).querySelectorAll('[help],[title]')].map(n => (n.getAttribute('help')||'') + '#' + (n.getAttribute('title')||'')).filter(s => s.replace(/#$/,'').length).slice(0,6);
            rows.push({help, chain: chain.slice(0,9)});
        }
        return JSON.stringify(rows, null, 1);
    }""")
    print(info)
    b.close()
