"""Diagnose: open M12205, Exhibits tab, click GO GET IT row0 modal, print modal + state."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("dialog", lambda d: d.accept())
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    box = pg.locator("#b0p0o254i0i0r1")
    box.click(); pg.wait_for_timeout(400)
    pg.keyboard.press("Control+a"); pg.keyboard.press("Delete")
    for ch in "M12205":
        pg.keyboard.press(ch); pg.wait_for_timeout(70)
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=40000)
    pg.wait_for_timeout(1200)
    pos = pg.evaluate("""() => { const t = [...document.querySelectorAll('button.fm-widget')].find(b => (b.textContent||'').trim().startsWith('Exhibits -')); const r = t.getBoundingClientRect(); return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)}; }""")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_function("() => /Found Count: \\d+/.test(document.body.innerText)", timeout=25000)
    pg.wait_for_timeout(1500)
    print("Found:", pg.evaluate("(document.body.innerText.match(/Found Count: \\d+/)||['?'])[0]"))
    rows = pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight)).map(el => {
        let p = el, rowtxt='';
        for (let i=0;i<8 && p;i++){ p = p.parentElement; if (p && /\\b\\d{5,6}\\b/.test(p.innerText||'') && /\\.[a-z0-9]{2,5}/i.test(p.innerText||'')) { rowtxt = p.innerText; break; } }
        const doc = (rowtxt.match(/\\b(\\d{5,6})\\b/)||[])[1] || null;
        const r = el.getBoundingClientRect();
        return [doc, Math.round(r.x+r.width/2), Math.round(r.y+r.height/2)];
    }))""")
    print("rows:", rows)
    import json
    items = json.loads(rows)
    d0, x0, y0 = items[0]
    pg.mouse.click(x0, y0)
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    print("modal buttons:", pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('.v-window .v-button')].map(b => ({cls: b.className.slice(0,60), t: b.innerText.trim()})))"""))
    pg.wait_for_timeout(1500)
    print("modal buttons +1.5s:", pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('.v-window .v-button')].map(b => ({cls: b.className.slice(0,80), t: b.innerText.trim()})))"""))
    b.close()
