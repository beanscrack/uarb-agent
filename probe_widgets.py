from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    info = pg.evaluate("""() => {
        const out = {widgets: [], editables: []};
        for (const e of document.querySelectorAll('.fm-widget, .v-widget')) {
            const t = (e.textContent||'').trim();
            if ((e.offsetWidth||e.offsetHeight) && t.length > 0 && t.length < 30)
                out.widgets.push(t + ' #' + e.id + '.' + e.className.slice(0,40));
        }
        for (const e of document.querySelectorAll('[contenteditable], .fm-textarea, .iwps_edit_box')) {
            const r = e.getBoundingClientRect();
            out.editables.push(e.tagName + '#' + e.id + '.' + e.className.slice(0,60) + ' ce=' + e.isContentEditable + ' sz=' + Math.round(r.width) + 'x' + Math.round(r.height) + ' txt=' + JSON.stringify((e.textContent||'').slice(0,20)));
        }
        return out;
    }""")
    for w in info["widgets"]: print("W:", w)
    for e in info["editables"]: print("E:", e)
    b.close()
