"""Golden-run guard: field identity must match the selectors the scraper hard-codes."""
import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(9000)
    info = pg.evaluate("""() => {
        const t = [...document.querySelectorAll('*')].find(e => (e.textContent||'').trim() === 'eg M01234' && !e.children.length);
        const box = t ? t.closest('[id]') : null;
        const btns = [...document.querySelectorAll('button.fm-widget')].map((e,i)=>[i,(e.textContent||'').trim().slice(0,20)]).filter(([ ,t]) => /^search/i.test(t));
        return JSON.stringify({box: box ? box.id : null, boxClass: box ? box.className : null, btns});
    }""")
    print(info)
    b.close()
