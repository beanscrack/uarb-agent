"""Compose a receiver-side reply preview: HTML manifest email + listing of ZIPS."""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agent_mail import build_bundle_html  # noqa: E402

z = sorted(glob.glob("C:/Users/fortn/task1/out*/**/manifest.json", recursive=True))
print("manifests:", z)
out_dir = Path("C:/Users/fortn/task1/uarb_agent/demo_src"); out_dir.mkdir(exist_ok=True)
for i, mf in enumerate(z[:3]):
    d = json.loads(Path(mf).read_text())
    meta = d.get("meta") or {}
    files = d.get("files") or []
    matter = d.get("matter") or meta.get("matter") or "MXXXXX"
    tab = d.get("tab") or (meta.get("tab") if isinstance(meta, dict) else None)
    for cand in (f"{matter} Exhibits", f"{matter} Key Documents", "Exhibits", "Key Documents", "Other Documents"):
        if cand in json.dumps(meta) if isinstance(meta, dict) else False:
            tab = cand.split(" ")[-1]
            break
    tab = tab or "Documents"
    html = build_bundle_html(meta, files, matter, tab)
    out = out_dir / f"reply_{i}_{matter}_{tab}.html"
    out.write_text(html, encoding="utf-8")
    print("wrote", out, len(files), "files")
