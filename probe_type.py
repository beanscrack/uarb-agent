"""Typing stress test (CDP key events, per-char): how many of M01234 / 12345 /
M12205 / abcde land in the matter field? Live page (known good)."""
import time

import browser_harness as bh


def type_via_cdp(ch):
    bh.cdp("Input.dispatchKeyEvent", type="keyDown", key=ch, text=ch, unmodifiedText=ch)
    bh.cdp("Input.dispatchKeyEvent", type="keyUp", key=ch)


bh.new_tab("https://uarb.novascotia.ca/fmi/webd/UARB15")
time.sleep(10)
pos = bh.js("""() => {
  const cands = [...document.querySelectorAll('.fm-textarea-content')].filter(e => (e.offsetWidth||e.offsetHeight));
  const b = cands[0]; const r = b.getBoundingClientRect();
  return JSON.stringify({x: r.x + r.width/2, y: r.y + r.height/2, id: (b.id||'').slice(-6)});
}""")
import json
p = json.loads(pos)
print("box", p, flush=True)
bh.cdp("Input.dispatchMouseEvent", type="mousePressed", x=int(p["x"]), y=int(p["y"]), button="left", clickCount=1)
bh.cdp("Input.dispatchMouseEvent", type="mouseReleased", x=int(p["x"]), y=int(p["y"]), button="left", clickCount=1)
time.sleep(0.5)

for s in ("M01234", "12345", "M12205", "abcde"):
    bh.cdp("Input.dispatchKeyEvent", type="keyDown", key="a", modifiers=2, code="KeyA")
    bh.cdp("Input.dispatchKeyEvent", type="keyUp", key="a", modifiers=2, code="KeyA")
    bh.cdp("Input.dispatchKeyEvent", type="keyDown", key="Delete", code="Delete")
    bh.cdp("Input.dispatchKeyEvent", type="keyUp", key="Delete", code="Delete")
    time.sleep(0.2)
    for ch in s:
        type_via_cdp(ch)
        time.sleep(0.07)
    got = bh.js("() => document.activeElement ? (document.activeElement.innerText||'').trim() : ''")
    print(f"wrote {s!r} -> field {got!r}", flush=True)
