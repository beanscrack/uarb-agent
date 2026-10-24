import base64, json
from playwright.sync_api import sync_playwright

HOOK = """
(() => {
  if (window.__dlHooked) return 'already';
  window.__dlHooked = true;
  window.__urls = [];
  window.__files = [];
  const o = window.open;
  window.open = function (u) {
    const url = String(u);
    window.__urls.push(url);
    fetch(url, {credentials: 'include'}).then(async (r) => {
      const buf = new Uint8Array(await r.arrayBuffer());
      let bin = '';
      for (let i = 0; i < buf.length; i += 8192)
        bin += String.fromCharCode.apply(null, buf.subarray(i, i + 8192));
      const cd = r.headers.get('content-disposition') || '';
      const m = cd.match(/filename\\*?=(?:UTF-8'')?'([^']+)'/);
      window.__files.push({url, status: r.status, name: m ? m[1] : url.split('/').pop(), size: buf.length, data: btoa(bin)});
    }).catch(e => window.__files.push({url, error: e.message}));
    return null;
  };
  return 'hooked';
})()
"""

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.goto("https://uarb.novascotia.ca/fmi/webd/UARB15", wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(8000)
    pg.evaluate(HOOK)
    box = pg.locator("#b0p0o254i0i0r1")
    box.click(); pg.wait_for_timeout(400)
    pg.keyboard.press("Control+a"); pg.keyboard.press("Delete")
    for ch in "M12205":
        pg.keyboard.press(ch); pg.wait_for_timeout(70)
    pg.locator("#b0p0o258i0i0r1").click()
    pg.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=30000)
    pg.wait_for_timeout(1200)
    pos = pg.evaluate("""() => { const t = [...document.querySelectorAll('button.fm-widget')].find(b => (b.textContent||'').trim().startsWith('Other Documents -')); const r = t.getBoundingClientRect(); return {x: r.x + r.width/2, y: r.y + r.height/2}; }""")
    pg.mouse.click(pos["x"], pos["y"])
    pg.wait_for_function("() => /Found Count: \\d+/.test(document.body.innerText)", timeout=20000)
    pg.wait_for_timeout(1500)
    print("rows:")
    rows = pg.evaluate("""() => {
        const out = [];
        for (const e of document.querySelectorAll('span.fm-text-character')) {
            const p = e.closest('.fm-text-paragraph');
        }
        // crude: take visible text chunks between 'Date' header and 'Download Files'
        return document.body.innerText.slice(0, 3000);
    }""")
    print(rows[:3000].replace("\n", " | "))

    # GO GET IT row 0
    p0 = pg.evaluate("""() => {
        const hits = [...document.querySelectorAll('div,span')].filter(e => e.children.length===0 && /GO GET IT/i.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
        let p = hits[0];
        for (let i=0;i<8 && p;i++){ p = p.parentElement; if (p && p.tagName === 'BUTTON') break; }
        const r = p.getBoundingClientRect();
        return {x: r.x + r.width/2, y: r.y + r.height/2};
    }""")
    pg.mouse.click(p0["x"], p0["y"])
    pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
    btn = pg.locator(".v-window .v-button:not(.v-disabled).fm-download-button")
    btn.wait_for(state="visible")
    # Route intercept: windows.open target goes through this (popups share context routes).
    captured = {}
    def route_handler(route):
        u = route.request.url
        print("ROUTE:", u[:120])
        captured["url"] = u
        if "/dl/" in u:
            captured["body"] = route.fetch().body()
        route.abort()
    pg.context.route("**/dl/**", route_handler)
    pg.context.route("**/webd/APP/**", route_handler)
    with pg.expect_event("popup", timeout=20000) as popinfo:
        btn.click()
    popup = popinfo.value
    print("popup url:", popup.url)
    pg.wait_for_timeout(3000)
    popup.close()
    print("captured keys:", list(captured.keys()), captured.get("url","")[:140])
    if "body" in captured:
        open("probe_dl_route.pdf", "wb").write(captured["body"])
        print("saved route body", len(captured["body"]))
    b.close(); import sys; sys.exit(0)
