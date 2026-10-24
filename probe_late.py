"""How long until the matter field appears after fresh goto? Poll layout markers."""
import sys, time
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    for t in range(30):
        pg.wait_for_timeout(2000)
        d = pg.evaluate("""() => {
            const b = [...document.querySelectorAll('button.fm-widget')].map(e => (e.textContent||'').trim().slice(0,18)).filter(x => x);
            const ready = b.includes('More Search Options') || b.some(x => x === 'Search');
            const cand = [...document.querySelectorAll('.fm-textarea-content')].filter(e => (e.offsetWidth||e.offsetHeight)).length;
            return JSON.stringify({sec: (document.body.innerText||'').trim().length, ready, cand});
        }""")
        print((t + 1) * 2, d, flush=True)
        if '"cand": 2' in d or '"cand": 1' in d:
            break
    b.close()
