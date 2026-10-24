"""Probe yesterday's UI page: dump network URLs + Find Records area DOM."""
import json
import time
from browser_harness.helpers import ensure_real_tab, js, page_info  # type: ignore

ensure_real_tab()
info = page_info()
print("url:", info["url"], "title:", info["title"])
txt = js("document.body.innerText.slice(0,400)")
print("body head:", txt.replace("\n", " | ")[:400])
# look for nav widgets
nav = js("""(() => {
  const hits = [...document.querySelectorAll('div,span,button,a')].filter(e => e.children.length === 0 && /Find Records|Back|Next|Search/i.test(e.textContent||'') && (e.offsetWidth||e.offsetHeight));
  return JSON.stringify(hits.map(e => (e.textContent||'').trim().slice(0,20)).slice(0,10));
})()""")
print("nav:", nav)
