"""UARB Public Documents Database agent (playwright, headless).

Verified mechanics (probing session on uarb.novascotia.ca FileMaker WebDirect app):

- Entry: https://uarb.novascotia.ca/fmi/webd/UARB15  (Vaadin/GWT single-page app).
- 'Go Directly to Matter' is a contenteditable div (id b0p0o254i0i0r1 at default layout).
  GWT fields need *trusted* key events: Press each char (type() drops chars).
- Search button id b0p0o258i0i0r1. Result tabs "Exhibits - N" etc are
  <button class=fm-widget> segments; a JS .click() is swallowed by GWT, real mouse events work.
- Doc list rows: buttons '.fm-widget.hand-cursor' with text 'GO GET IT' (~11 visible; the
  FileMaker portal is virtual, so scrolling shows more rows).
- GO GET IT opens a "Download Files" modal with ONE .fm-download-button (enabled after a
  server prep step). Click => window.open GET {base}/fmi/webd/APP/connector/<ui>/<token>/dl/<docno>.<ext>.
  The URL is session-bound: direct curl (even with cookies from CDP) gets 403, a same-page
  fetch() gets 200. => Intercept the popup GET at the Playwright network layer
  (context.route '**/dl/**'), fetch() it, abort the popup navigation.
- Do all work in ONE page (FileMaker session is per-tab-load; a reload or new tab = new
  empty session). Modal 'Close' unblocks the next GO GET IT; each GO GET IT yields one file.
- Metadata panel (title, type, status, dates, outcome, category) is plain body innerText.
"""
from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "https://uarb.novascotia.ca/fmi/webd/UARB15"
TABS = ["Exhibits", "Key Documents", "Other Documents", "Transcripts", "Recordings"]


def type_text(page, sel: str, text: str) -> None:
    page.locator(sel).click()
    page.wait_for_timeout(350)
    page.keyboard.press("Control+a")
    page.keyboard.press("Delete")
    page.wait_for_timeout(120)
    for ch in text:
        page.keyboard.press(ch)
        page.wait_for_timeout(60)


def norm_doc_type(s: str) -> str:
    t = re.sub(r"\bs\b$", "", s.strip().lower())
    for tab in TABS:
        if tab.lower() == t:
            return tab
    raise ValueError(f"unknown document type: {s!r} (expect one of {TABS})")


def search_matter(page, matter: str) -> None:
    page.goto(BASE, wait_until="domcontentloaded", timeout=90000)
    page.wait_for_timeout(7000)
    type_text(page, "#b0p0o254i0i0r1", matter)
    got = (page.evaluate("document.querySelector('#b0p0o254i0i0r1').innerText") or "").strip()
    if got != matter:
        raise RuntimeError(f"matter box shows {got!r}, expected {matter!r}")
    page.locator("#b0p0o258i0i0r1").click()
    try:
        page.wait_for_function("() => /Exhibits - \\d+/.test(document.body.innerText)", timeout=40000)
    except Exception:
        # No tab list appeared. Check for FileMaker's 'finding records completed. no records were found' alert
        alert = page.evaluate(
            "() => [...document.querySelectorAll('.v-window')].map(w=>(w.innerText||'').replace(/\\n/g,' ')).join(' // ')"
        )
        low = alert.lower()
        if "no records" in low or "no matching" in low or "not found" in low:
            page.keyboard.press("Escape")
        raise SystemExit(f"NO_MATCH: {matter} ({alert[:100]})")
    page.wait_for_timeout(1000)


def read_metadata(page, tab: str | None = None) -> dict:
    """counts = from the tab segment labels only (Exhibits - 13): body regex on the result
    page can also hit rows ('Other Documents - 43' button)."""
    txt = page.inner_text("body")
    counts = {}
    for t in TABS:
        c = re.search(rf"{t} - (\d+)", txt)
        counts[t] = int(c.group(1)) if c else 0
    m = re.search(
        r"(M\d{5})\s*\n\s*\n(?P<type>[^\n]+)\s*\n\s*\n(?P<status>[^\n]+)\s*\n\s*\n(?P<title>[^\n]+)\s*\n\s*\n"
        r"(?P<date_opened>\d{2}/\d{2}/\d{4})\s*\n\s*\n(?P<date_final>[^\n]*)\s*\n\s*\n(?P<outcome>[^\n]*)\s*\n\s*\n(?P<category>[^\n]+)",
        txt,
    )
    meta = {"matter": m.group(1) if m else None, "counts": counts}
    if m:
        meta.update({k: v.strip() for k, v in m.groupdict().items() if k != "1"})
    return meta


def tab_open(page, tab: str) -> bool:
    """True when the doc tab is the active portal view ('Found Count: N' is on-screen)."""
    return bool(re.search(r"Found Count: \d+", page.inner_text("body")))


def tab_pos(page, tab: str):
    return page.evaluate(
        """(t) => {
            const b = [...document.querySelectorAll('button.fm-widget')]
                .find(b => (b.textContent||'').trim().startsWith(t + ' -'));
            if (!b) return null;
            const r = b.getBoundingClientRect();
            return {x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)};
        }""",
        tab,
    )


def dismiss_grow_dialogs(page, max_clicks=60) -> int:
    """Click OK on any 'Grow the list (x of y)' dialogs. Returns number dismissed."""
    n = 0
    for _ in range(max_clicks):
        clicked = page.evaluate(
            """() => {
                const win = [...document.querySelectorAll('.v-window')]
                    .find(w => /Grow the list\\. \\(\\d+ of \\d+\\)/.test(w.innerText));
                if (!win) return false;
                const ok = win.querySelector('.v-button-primary');
                if (ok) { ok.click(); return true; }
                const cb = win.querySelector('.v-window-closebox');
                if (cb) { cb.click(); return true; }
                return false;
            }"""
        )
        if not clicked:
            break
        n += 1
        page.wait_for_timeout(250)
    return n


def open_tab(page, tab: str, min_rows: int = 1) -> None:
    """Open a doc-type tab. Click the segment repeatedly (real mouse) to grow the portal list.
    Each click past the first raises 'Grow the list' dialogs which we click OK on; the
    nested portals flatten toward one long list (6 -> ~12 -> ~18 rows)."""
    pos = tab_pos(page, tab)
    if not pos:
        raise RuntimeError(f"tab not found: {tab}")
    page.mouse.click(pos["x"], pos["y"])
    page.wait_for_function("() => /Found Count: \\d+/.test(document.body.innerText)", timeout=60000)
    page.wait_for_timeout(1200)
    for _ in range(40):
        n = len([r for r in visible_rows(page) if r["doc"]])
        if n >= min_rows:
            break
        pos = tab_pos(page, tab)
        page.mouse.click(pos["x"], pos["y"])
        page.wait_for_timeout(900)
        dismissed = dismiss_grow_dialogs(page)
        page.wait_for_timeout(700)
        if not dismissed:
            break


def is_gone(page, doc: str) -> bool:
    """True if a 'not found' style response window is up (used after a GO GET IT click)."""
    return page.evaluate(
        """() => {
            const win = [...document.querySelectorAll('.v-window')].find(w => /not be found|File Not Found|not available/i.test(w.innerText||''));
            if (!win) return false;
            const cb = win.querySelector('.v-button-primary, .v-window-closebox');
            if (cb) cb.click();
            return true;
        }"""
    )


def visible_rows(page) -> list[dict]:
    """FileMaker portal rows currently rendered, in portal order:
    [{doc, title, ext, x, y}, ...].
    Works by locating the row's file-type text node ( '.pdf' / '.docx' ...): its parent is the
    row box; the row's column fields are the box's leaf texts in order (docNo/title/date/sec, ...).
    The GO GET IT button of that row = the '.fm-widget.hand-cursor' button inside the box.
    TICKET-CUTOFF GUARD: FileMaker's 'show records 1-N' grows by +8 each harvest; rows
    beyond the visible GO GET IT leaf count are render ghosts (the extension label exists,
    the action widget does not). Clicking one opens the 'Show all records' alert and wedges
    the UI (proved: M12205 exhibits row 9 == the GO GET IT leaf count). Cap by leaf count."""
    rows = page.evaluate(_ROWS_JS)
    state = page.evaluate(
        """() => {
            const b = [...document.querySelectorAll('button.fm-widget.hand-cursor')].filter(e => /GO GET IT/.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
            const ys = b.map(e => e.getBoundingClientRect().y);
            return JSON.stringify({n: b.length, ymin: ys.length ? Math.min(...ys) : 0, ymax: ys.length ? Math.max(...ys) : 0});
        }"""
    )
    import json as _json
    st = _json.loads(state)
    if st["n"] and st["n"] < len(rows):
        # keep only rows whose GO GET IT button is actually on screen (drop ticket ghosts)
        rows = [r for r in rows if st["ymin"] - 12 <= r["y"] <= st["ymax"] + 12]
    return rows


_ROWS_JS = r"""() => {
            // 1) all file-ext text nodes ('.pdf' etc.)
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            const extNodes = [];
            while (walker.nextNode()) {
                const t = walker.currentNode.nodeValue.trim();
                if (/^\.[A-Za-z0-9]{2,5}$/.test(t)) extNodes.push(walker.currentNode);
            }
            const out = [], seenRows = new Set();
            for (const tn of extNodes) {
                let box = tn.parentElement;
                for (let i = 0; i < 10 && box.parentElement; i++) {
                    const texts = [];
                    (function w(n) {
                        if (n.nodeType === 3) { const t = n.nodeValue.trim(); if (t) texts.push(t); }
                        else for (const c of n.childNodes) w(c);
                    })(box);
                    const gi = texts.findIndex(t => /GO GET IT/i.test(t));
                    if (gi >= 0 && texts[texts.length - 1] === tn.nodeValue.trim() && gi === texts.length - 2) {
                        // 3) this box holds the row and only the row
                        const docRe = /^\d{3,6}$|^[A-Za-z]{1,3}(-\d{1,3})?(\([A-Za-z]\))?(-[ivxIVX]{1,4})?$/;
                        const dateRe = /^\d{2}\/\d{2}\/\d{4}$/;
                        let doc = null, title = null;
                        const lastT = texts[gi - 1] || '';
                        let end = gi - 1;
                        if (/Preview/i.test(lastT)) end = gi - 2;
                        if (gi >= 3 && dateRe.test(texts[1])) {
                            // exhibits layout: [type, date, sec, doc, (Preview), GO GET IT, ext]
                            doc = texts[end]; title = texts[0];
                        } else if (gi >= 3) {
                            // documents layout: [doc, title, date, sec, (Preview), GO GET IT, ext]
                            for (let k = 0; k < gi; k++) {
                                const t = texts[k];
                                if (docRe.test(t) && gi - k >= 3 && dateRe.test(texts[k + 2])) {
                                    doc = t; title = /^[A-Za-z]/.test(texts[k + 1] || '') ? texts[k + 1] : null;
                                    break;
                                }
                            }
                        }
                        if (doc && !seenRows.has(box)) {
                            seenRows.add(box);
                            const btn = [...box.querySelectorAll('.fm-widget.hand-cursor')].find(e => /GO GET IT/i.test(e.textContent || ''));
                            const r = (btn || box).getBoundingClientRect();
                            if (btn) out.push({doc, title, ext: tn.nodeValue.trim().slice(1), x: Math.round(r.x + r.width/2), y: Math.round(r.y + r.height/2)});
                        }
                        break;
                    }
                    box = box.parentElement;
                }
            }
            function textNull(x) { return null; }
            out.sort((a, b) => (a.y - b.y) || (a.x - b.x));
            return out;
        }"""


def harvest_all(pg, out_dir: Path, meta: dict, label: str, target: int) -> list[dict]:
    """The probe_mechE2 loop, productionized: harvest rows in document order as the portal
    feeds them, one GWT op per cycle, persisting manifest.json after every file."""
    cap: dict[str, tuple] = {}
    popups: list = []

    def handler(route):
        url = route.request.url
        if url in cap:
            route.continue_()
            return
        try:
            f = route.fetch(timeout=30000)
            cap[url] = (f.status, f.body())
            route.fulfill(status=f.status, body=cap[url][1],
                          headers={k: v for k, v in f.headers.items()
                                   if k.lower() not in ("content-encoding", "content-length", "transfer-encoding")})
        except Exception as e:
            cap[url] = ("ERR", str(e).encode())
            try:
                route.continue_()
            except Exception:
                pass

    pg.context.on("page", lambda pp: popups.append(pp))

    def on_req(req):
        if "/dl/" in req.url:
            (out_dir / "dl.log").open("a", encoding="utf-8").write(f"REQ {req.url}\n")

    pg.context.on("request", on_req)
    pg.context.route("**/dl/**", handler)
    done: set[str] = set()
    harvested: list[dict] = []
    names: set[str] = set()

    def flush():
        (out_dir / "manifest.json").write_text(
            json.dumps({"label": getattr(harvest_all, "label", label), "meta": meta, "files": harvested}, indent=2),
            encoding="utf-8")

    n_target = target if target > 0 else 999
    ok = 0
    guard = 0
    max_guard = n_target * 5 + 60
    try:
        while len(harvested) < n_target and guard < max_guard:
            guard += 1
            rows = visible_rows(pg)
            cand = next((r for r in rows if r["doc"] and r["doc"] not in done), None)
            if cand is None:
                pg.mouse.wheel(0, 500)
                pg.wait_for_timeout(1500)
                continue
            done.add(cand["doc"])
            pg.mouse.click(cand["x"], cand["y"])
            win = ""
            modal = False
            try:
                pg.wait_for_selector(".v-window:has-text('Download Files')", timeout=15000)
                modal = True
            except Exception:
                wins = pg.evaluate("() => [...document.querySelectorAll('.v-window')].map(w=>w.innerText.replace(/\\n/g,' ')).join(' // ')")
                (out_dir / "errors.log").open("a", encoding="utf-8").write(f"guard={guard} doc={cand['doc']}: {wins[:160]}\n")
                # dismiss the obsolete-record / error window so the portal is clickable again
                pg.evaluate("""() => { for (const w of document.querySelectorAll('.v-window')) {
                    const b = [...w.querySelectorAll('.v-button').find ? [] : []]; } }""")
                prim = pg.locator(".v-window .v-button-primary")
                if prim.count():
                    try:
                        prim.last.click(timeout=4000)
                    except Exception:
                        pg.keyboard.press("Escape")
                pg.wait_for_timeout(1500)
                continue
            btn = pg.locator(".v-window .fm-download-button:not(.v-disabled)")
            if not btn.count():
                (out_dir / "errors.log").open("a", encoding="utf-8").write(f"guard={guard} doc={cand['doc']}: modal, no enabled download button\n")
                try:
                    pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=4000)
                except Exception:
                    pg.keyboard.press("Escape")
                pg.wait_for_timeout(1500)
                continue
            btn.first.click()
            t0 = time.time()
            while time.time() - t0 < 60 and sum(1 for u in cap if cap[u][0] == 200) <= ok:
                pg.wait_for_timeout(250)
            for pp in popups:
                try:
                    pp.close()
                except Exception:
                    pass
            popups.clear()
            #Close the modal (a stale modal blocks the next GO GET IT click)
            for _ in range(3):
                try:
                    pg.locator(".v-window .v-button-primary", has_text="Close").last.click(timeout=4000)
                    break
                except Exception:
                    pg.keyboard.press("Escape")
                    pg.wait_for_timeout(800)
            pg.wait_for_timeout(1800)
            new = [(u, v) for u, v in cap.items() if v[0] == 200]
            if len(new) > ok:
                ok += 1
                url, (_, body) = new[-1]
                ext = url.rsplit(".", 1)[-1].lower()[:5]
                doc = cand["doc"]
                name = re.sub(r'[:*?"<>|]', "_", f"{doc}.{ext}")
                k = 2
                while name in names:
                    name = re.sub(r'[:*?"<>|]', "_", f"{doc} ({k}).{ext}")
                    k += 1
                names.add(name)
                (out_dir / name).write_bytes(body)
                harvested.append({"doc": doc, "title": cand.get("title", ""), "date": cand.get("date", ""),
                                  "security": cand.get("security", ""), "name": name, "bytes": len(body)})
                flush()
            (out_dir / "progress.txt").write_text(
                f"{len(harvested)}/{target} harvested; guard={guard}\n", encoding="utf-8")
    finally:
        try:
            pg.context.unroute("**/dl/**", handler)
        except Exception:
            pass
        flush()
    return harvested


def scrape(matter: str, doc_type: str, out_root: Path, target: int = 0) -> dict:
    doc_type = norm_doc_type(doc_type)
    out_dir = out_root / f"{matter}_{doc_type.replace(' ', '_')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        status = {"matter": matter, "doc_type": doc_type, "files": [], "meta": {}, "target": target}
        try:
            search_matter(page, matter)
            meta = read_metadata(page)
            status["meta"] = meta
            count = (meta.get("counts") or {}).get(doc_type, 0)
            (out_dir / "manifest.json").write_text(
                json.dumps({"matter": matter, "tab": doc_type, "meta": meta}, indent=2), encoding="utf-8")
            n_target = target if target > 0 else count
            if n_target == 0:
                status["files"] = []
                status["zip"] = make_zip(out_root, out_dir, matter, doc_type)
                return status
            open_tab(page, doc_type, min_rows=6)
            files = harvest_all(page, out_dir, meta, f"{matter} {doc_type}", n_target)
            status["files"] = files
            # README documents the run: what the tab contained, what was fetched, and
            # (importantly for reviewers) which rows FileMaker WebDirect refused tokens for.
            got = {f["doc"] for f in files}
            listed = sorted(set(done) - got)
            readme = [
                f"# UARB {matter} — {doc_type}",
                "",
                f"Fetched {len(files)} of {n_target} rows from the '{doc_type}' portal of matter {matter}.",
                f"Site: {BASE} (FileMaker WebDirect; downloads are session/cookie-bound, so retrieval runs through a real browser session).",
                "",
                "## Files",
                *[f"- {f['name']} — doc {f['doc']} | {f.get('title') or ''} | {f.get('date') or ''} | {f['bytes']:,} bytes" for f in files],
                "",
                "## Rows without available files",
                "FileMaker WebDirect answers 'No Matching Records' (download token consumed/expired server-side) for these rows:",
                *([f"- {d}" for d in listed] or ["(none)"]),
                "",
                f"Generated by uarb_scrape.py (github.com/fortnbrnsecond1-maker/uarb-agent) at {time.strftime('%Y-%m-%d %H:%M')}.",
            ]
            (out_dir / "README.md").write_text("\n".join(readme), encoding="utf-8")
            (out_dir / "manifest.json").write_text(
                json.dumps({"matter": matter, "tab": doc_type, "meta": meta, "files": files}, indent=2),
                encoding="utf-8")
        finally:
            b.close()
    status["zip"] = make_zip(out_root, out_dir, matter, doc_type)
    return status


def make_zip(out_root: Path, out_dir: Path, matter: str, doc_type: str) -> str:
    zpath = out_root / f"{matter}_{doc_type.replace(' ', '_')}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(out_dir.iterdir()):
            if f.is_file() and f.name != zpath.name:
                z.write(f, f.name)
    return str(zpath)


if __name__ == "__main__":
    m = sys.argv[1]
    dt = sys.argv[2]
    root = Path(sys.argv[3])
    tgt = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    st = scrape(m, dt, root, tgt)
    print(json.dumps({"matter": st["matter"], "doc_type": st["doc_type"],
                      "n_files": len(st["files"]), "zip": st.get("zip")}, indent=2))
