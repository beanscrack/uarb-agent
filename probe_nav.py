from playwright.sync_api import sync_playwright

BASE = "https://uarb.novascotia.ca/fmi/webd/UARB15"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto(BASE, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)

    box = pg.locator("#b0p0o254i0i0r1")
    box.click()
    pg.wait_for_timeout(500)
    # focus is inside a GWT field: clear, then type char-by-char with pauses
    pg.keyboard.press("Control+a")
    pg.keyboard.press("Delete")
    pg.wait_for_timeout(200)
    for ch in "M12205":
        pg.keyboard.press(ch)
        pg.wait_for_timeout(80)
    # ensure 'M' landed (GWT misses first char sometimes)
    val = pg.evaluate("document.querySelector('#b0p0o254i0i0r1').innerText")
    if not val.startswith("M"):
        print("refill M, had:", repr(val))
        pg.keyboard.press("Home")
        pg.keyboard.press("M")
        pg.wait_for_timeout(100)
    print("field after type:", pg.evaluate("document.querySelector('#b0p0o254i0i0r1').innerText"))
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=30000)
    print("SEARCH OK")
    print(pg.inner_text("body")[:400].replace("\n", " | "))

    # tabs row
    pg.locator("div.fm-widget", has_text="Other Documents -").first.click()
    pg.wait_for_timeout(3000)
    print("TAB OK, found:", pg.evaluate("() => (document.body.innerText.match(/Found Count: \\d+/)||['?'])[0]"))

    # GO GET IT row0 via leaf-click emulation
    pg.evaluate("""() => {
        const hits = [...document.querySelectorAll('div,span')].filter(e => e.children.length===0 && /GO GET IT/i.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        hits[0].closest('.fm-widget-hand-cursor, .fm-widget, .v-widget').click();
        hits[0].click();
    }""")
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    print("MODAL OK")
    st = pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('.v-window .fm-download-button')].map(b => ({cls: b.className.slice(0,60), t: b.innerText})))""")
    print("buttons:", st)
    pg.wait_for_timeout(1500)
    st2 = pg.evaluate("""() => JSON.stringify([...document.querySelectorAll('.v-window .fm-download-button')].map(b => ({cls: b.className.slice(0,60), t: b.innerText})))""")
    print("buttons after 1.5s:", st2)
    b.close()
