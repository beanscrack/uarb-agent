import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, ".")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    box = pg.locator("#b0p0o254i0i0r1")
    def type_box(text):
        box.click()
        pg.wait_for_timeout(400)
        pg.keyboard.press("Control+a"); pg.keyboard.press("Delete")
        pg.wait_for_timeout(150)
        for ch in text:
            pg.keyboard.press(ch); pg.wait_for_timeout(70)
        v = (pg.evaluate("document.querySelector('#b0p0o254i0i0r1').innerText") or "").strip()
        if v != text:
            print("field drift:", repr(v), "-> retry full")
            pg.keyboard.press("Control+a"); pg.keyboard.press("Delete")
            pg.wait_for_timeout(150)
            for ch in text:
                pg.keyboard.press(ch); pg.wait_for_timeout(90)
            v = (pg.evaluate("document.querySelector('#b0p0o254i0i0r1').innerText") or "").strip()
        return v
    assert type_box("M12205") == "M12205"
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=30000)
    pg.wait_for_timeout(1500)

    # Inspect tab widget class and click home tab first, then Other Documents
    tabs = pg.evaluate("""() => {
        const acc = [];
        for (const e of document.querySelectorAll('*')) {
            const t = (e.textContent||'').trim();
            if (e.children.length === 0 && /^(Exhibits|Key Documents|Other Documents|Transcripts|Recordings) - \\d+$/.test(t)) {
                let p = e, chain = [];
                for (let i=0;i<6 && p;i++){ chain.push(p.tagName + '#' + p.id + '.' + (p.className||'').toString().split(' ').slice(0,3).join('.')); p = p.parentElement; }
                const r = e.getBoundingClientRect();
                acc.push({t, x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2), chain});
            }
        }
        return acc;
    }""")
    for x in tabs: print(x)
    b.close()
