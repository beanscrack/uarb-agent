"""Why did Key Documents run hang at search? headless search page: metrics, buttons."""
import sys
sys.path.insert(0, ".")
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(9000)
    d = pg.evaluate("""() => {
        const tabs = [...document.querySelectorAll('button.fm-widget')].map(e => (e.textContent||'').trim().slice(0,18)).filter(t => t);
        const tas = [...document.querySelectorAll('.fm-textarea-content')].map((e,i) => ({id: e.id, vis: !!(e.offsetWidth||e.offsetHeight), ph: e.placeholder}));
        const bodyLen = (document.body.innerText||'').trim().length;
        return JSON.stringify({tabs: tabs.slice(0,14), tas, bodyLen, url: location.href.slice(-40)});
    }""")
    print(d)
    b.close()
