import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    box = pg.locator("#b0p0o254i0i0r1")
    box.click(); pg.wait_for_timeout(400)
    pg.keyboard.press("Control+a"); pg.keyboard.press("Delete")
    for ch in "M12205":
        pg.keyboard.press(ch); pg.wait_for_timeout(70)
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=30000)
    pg.wait_for_timeout(1200)
    # click the tab button element via real mouse (GWT needs trusted events)
    pos = pg.evaluate("""() => {
        const t = [...document.querySelectorAll('button.fm-widget')].find(b => (b.textContent||'').trim().startsWith('Other Documents -'));
        if (!t) return null;
        const r = t.getBoundingClientRect();
        return {x: r.x + r.width/2, y: r.y + r.height/2};
    }""")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_function("() => /Found Count: \\d+/.test(document.body.innerText)", timeout=20000)
    pg.wait_for_timeout(1500)
    print("TAB OK:", pg.evaluate("(document.body.innerText.match(/Found Count: \\d+/)||['?'])[0]"))

    # GO GET IT widgets
    g = pg.evaluate("""() => {
        const hits = [...document.querySelectorAll('div,span')].filter(e => e.children.length===0 && /GO GET IT/i.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        return JSON.stringify(hits.map(e => {
            let p = e, root = null;
            for (let i=0;i<8 && p;i++){ p = p.parentElement; if (p && p.className && /fm-widget/.test(p.className||'')) root = p; }
            const r = (root||e).getBoundingClientRect();
            return {root: root ? root.tagName + '#' + root.id + '.' + (root.className||'').toString().split(' ').slice(0,4).join('.') : null, x: Math.round(r.x+r.width/2), y: Math.round(r.y+r.height/2)};
        }));
    }""")
    print("GGI:", g)
    # click first GO GET IT using bounding via Playwright mouse (CDP)
    import json
    items = json.loads(g)
    pg.mouse.click(items[0]["x"], items[0]["y"])
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    print("MODAL OK:", pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('.v-window .fm-download-button')].map(b => ({cls: b.className.slice(0,80), t: b.innerText})))"""))
    b.close()
