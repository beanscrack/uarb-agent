"""Build demo_uarb_agent.mp4 (~110s). Rich evidence: real screenshots, code walk,
email in/out, ZIP listing, interstitial flips through rows. ASCII captions."""
import subprocess
from pathlib import Path

SCR = Path(__file__).parent
TMP = SCR / "demo_frames"
SRC = SCR / "demo_src"
TMP.mkdir(exist_ok=True)
OUT = SCR.parent / "demo_uarb_agent.mp4"
FF = r"C:/Users/fortn/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe"
FONT = "'C\\:/Windows/Fonts/arialbd.ttf'"

CODE = SCR / "uarb_scrape.py"
MAIL = SCR / "agent_mail.py"


def P(name):
    p = SRC / name
    return str(p) if p.exists() else None


def txt_slide(lines):
    return [(t, sz, x, y, c) for (t, sz, x, y, c) in lines]


slides = [
    (6, None, [
        ("UARB PUBLIC-DOCS AGENT", 58, 60, 50, "white"),
        ("Co-op Technical Assignment  -  Winter 2027", 30, 60, 130, "0x9fc7ff"),
        ("email in -> matter search -> doc counting -> downloads -> ZIP reply", 26, 60, 180, "0xcfe6ff"),
        ("full stack: Python + Playwright (no API this site has)", 24, 60, 215, "0x9fe8c0"),
    ]),
    (8, None, [
        ("THE PROBLEM", 50, 60, 50, "white"),
        ("staff copy UARB PDFs by hand: find matter -> open tabs ->", 28, 60, 140, "0xcfe6ff"),
        ("click GO GET IT per doc -> zip -> attach -> reply.", 28, 60, 178, "0xcfe6ff"),
        ("site: FileMaker WebDirect (GWT app, Java plugin heritage):", 26, 60, 226, "0x9fc7ff"),
        ("no REST, no clean DOM, no keyboard events, per-IP sessions.", 26, 60, 262, "0x9fc7ff"),
    ]),
    (7, None, [
        ("STEP 1  EMAIL IN", 50, 60, 50, "white"),
        ("agent_mail.py  --  watch: IMAP poll loop", 30, 60, 140, "0xcfe6ff"),
        ("subject/body -> regex M\\d{5} + longest doc-phrase", 28, 60, 182, "0xcfe6ff"),
        ("seen.json bookkeeping, allow-list, In-Reply-To threading.", 26, 60, 220, "0xcfe6ff"),
    ]),
    (9, None, [
        ("REQUEST PARSER (agent_mail.py)", 40, 60, 50, "white"),
        ("matter = regex(M[0-9]{5}, subject + body)", 27, 60, 130, "white"),
        ("doc type = longest phrase: 'key documents' beats 'documents'", 26, 60, 168, "white"),
        ("tests: 'give me exhibits from m12383' ->  M12383 / Exhibits  OK", 25, 60, 206, "white"),
        ("        'key documents M12383'             ->  M12383 / Key     OK", 25, 60, 240, "white"),
    ]),
    (8, P("01_search.png"), [
        ("STEP 2  SITE NAVIGATION", 44, 20, 30, "white"),
        ("matter field = contenteditable DIV, not an input.", 28, 20, 92, "white"),
        ("untrusted .value writes get swallowed by GWT.", 26, 20, 128, "white"),
        ("trusted CDP per-char key events + read-back validation.", 26, 20, 162, "white"),
    ]),
    (4, P("02_typed.png"), [("MATTER FIELD: typed + verified", 34, 20, 840, "white")]),
    (6, P("06_result2.png"), [
        ("SEARCH -> result record tabs", 40, 20, 30, "white"),
        ("tab labels carry the counts  -  read from the Chrome a11y tree", 24, 20, 92, "white"),
    ]),
    (6, P("03_result.png"), [
        ("STEP 3  DOC COUNTING + METADATA", 44, 20, 30, "white"),
        ("Exhibits 13, Key 6, Other 43, Transcripts 0, Recordings 0", 26, 20, 92, "white"),
    ]),
    (7, P("07_portal_exhibits.png"), [
        ("portal rows: virtual rendered, x ~ 8", 40, 20, 30, "white"),
        ("rows = grid skin, leaf-text walking finds them, not DOM rows", 26, 20, 92, "white"),
    ]),
    (8, P("08_ready1.png"), [
        ("STEP 4  THE DOWNLOAD MACHINE", 44, 20, 30, "white"),
        ("row click -> Download Files modal -> /dl/ popup", 26, 20, 92, "white"),
        ("modal HTML has NO URL - server mints it on click", 24, 20, 126, "white"),
    ]),
    (9, P("09_ready2.png"), [
        ("THE WALL (the honest part)", 44, 20, 30, "white"),
        ("tokens per row + session, then server: No Matching Records", 26, 20, 92, "white"),
        ("at row 9: the 8-row portal page locks the harvest", 24, 20, 126, "white"),
        ("(session 1: 8/13, session 2 cold probe: 2/13, run12: 10/43)", 24, 20, 160, "0xffd6a5"),
    ]),
    (8, None, [
        ("MECHANISM FINDING  -  HOW I GOT HERE", 40, 60, 50, "white"),
        ("logged every FINOMResRpc payload -> URL tokens A/B counters", 27, 60, 140, "0xcfe6ff"),
        ("viewport height x grow-click x open-mode matrix", 27, 60, 178, "0xcfe6ff"),
        ("probe_mechA..E: direct fetch 403; route.fetch WITH cookies OK", 27, 60, 216, "0xcfe6ff"),
        ("Lesson saved: skill filemaker-webdirect-scraping", 26, 60, 258, "0x9fe8c0"),
    ]),
    (7, P("11_keydocs.png"), [
        ("re-run for other doc tabs is one click choice", 34, 20, 30, "white"),
        ("Key Documents - 6  fully harvested", 26, 20, 92, "white"),
    ]),
    (8, P("12_otherdocs.png"), [
        ("Other Documents - 43 (the biggest tab)", 34, 20, 30, "white"),
        ("same machine: first 8-10 rows, rest logged as refused", 26, 20, 92, "white"),
    ]),
    (7, None, [
        ("STEP 6  ZIP + REPLY OUT", 50, 60, 50, "white"),
        ("ZIP: PDFs + manifest.json + README (counts + refused rows).", 28, 60, 150, "0xcfe6ff"),
        ("reply email: plain + HTML manifest table + ZIP, in-thread.", 26, 60, 190, "0xcfe6ff"),
        ("agent: reply body from metadata: what the matter IS, not just files", 26, 60, 226, "0xcfe6ff"),
    ]),
    (8, None, [
        ("WHAT I LEARNED", 50, 60, 50, "white"),
        ("probe the mechanism, not the markup: RPC decode + matrix", 27, 60, 140, "0xcfe6ff"),
        ("found the minted-token wall for real, not from docs.", 27, 60, 178, "0xcfe6ff"),
        ("reproducible demo beats polished claims.", 27, 60, 216, "0xcfe6ff"),
        ("code: github.com/fortnbrnsecond1-maker/uarb-agent", 24, 60, 262, "0x9fe8c0"),
    ]),
]

idx = 0
total = 0.0
for dur, img, texts in slides:
    base = [FF, "-y"]
    if img:
        base += ["-loop", "1", "-framerate", "10", "-t", str(dur), "-i", img]
    else:
        base += ["-f", "lavfi", "-i", f"color=c=0x0b1020:s=1600x900:d={dur}:r=10"]
    vf = ["scale=1600:900:force_original_aspect_ratio=decrease",
          "pad=1600:900:'(ow-iw)/2':'(oh-ih)/2'"]
    for t, size, x, y, col in texts:
        assert t.isascii(), f"non-ascii caption: {t!r}"
        esc = t.replace(":", "\\:")
        vf.append(f"drawtext=fontfile={FONT}:text='{esc}':fontsize={size}:fontcolor={col}:x={x}:y={y}")
    out = TMP / f"s{idx:02d}.mp4"
    cmd = base + ["-vf", ",".join(vf), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-t", str(dur), str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print("FAIL slide", idx)
        print(r.stderr[-700:])
        raise SystemExit(1)
    idx += 1
    total += dur

ls = TMP / "list.txt"
ls.write_text("\n".join(f"file 's{i:02d}.mp4'" for i in range(idx)), encoding="utf-8")
subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", str(ls), "-c", "copy", str(OUT)], check=True, capture_output=True)
print("wrote", OUT, OUT.stat().st_size, "bytes;", total, "sec")
