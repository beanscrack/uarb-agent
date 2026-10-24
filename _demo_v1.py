"""Build demo_uarb_agent.mp4 (~73s) from live evidence + ffmpeg text overlays.
Slides use real screenshots (demo_src) when present, dark text slides otherwise."""
import subprocess
from pathlib import Path

SCR = Path(__file__).parent
TMP = SCR / "demo_frames"
SRC = SCR / "demo_src"
TMP.mkdir(exist_ok=True)
OUT = SCR.parent / "demo_uarb_agent.mp4"
FF = r"C:/Users/fortn/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-9.0.1-full_build/bin/ffmpeg.exe"

P = lambda name: str(SRC / name) if (SRC / name).exists() else None

slides = [
    (6, None, [
        ("UARB PUBLIC-DOCS AGENT", 58, 60, 60, "white"),
        ("Co-op Technical Assignment Winter 2027", 30, 60, 140, "0x9fc7ff"),
        ("an agent that answers requests against the Nova Scotia UARB database", 26, 60, 190, "0xcfe6ff"),
    ]),
    (7, None, [
        ("1 - EMAIL REQUEST", 50, 60, 60, "white"),
        ("staff mails:  \"give me the Exhibits for M12205\"", 30, 60, 150, "0xcfe6ff"),
        ("agent_mail.py polls IMAP, parses Matter + doc type,", 26, 60, 200, "0xcfe6ff"),
        ("threads replies via In-Reply-To, allow-list + seen bookkeeping.", 26, 60, 236, "0xcfe6ff"),
    ]),
    (8, P("01_search.png"), [
        ("2 - WEBSITE NAVIGATION", 44, 60, 60, "white"),
        ("FileMaker WebDirect (GWT): no REST, no normal DOM inputs.", 26, 60, 120, "white"),
        ("Playwright + trusted events: per-char typing into the", 24, 60, 158, "white"),
        ("contenteditable field, real mouse clicks on tabs.", 24, 60, 190, "white"),
    ]),
    (5, P("02_typed.png"), [
        ("MATTER FIELD: TYPED, VERIFIED", 40, 60, 60, "white"),
        ("field value read back == M12205 before Search is clicked", 24, 60, 120, "white"),
    ]),
    (6, P("03_result.png"), [
        ("3 - DOC COUNTING", 44, 60, 60, "white"),
        ("counts from tab labels: Exhibits 13 - Key 6 - Other 43", 26, 60, 125, "white"),
        ("metadata: type/status/title/dates/category of the matter", 24, 60, 162, "white"),
    ]),
    (6, P("04_exhibits.png"), []),
    (9, P("05_modal.png"), [
        ("4 - DOWNLOADING, THE HARD PART", 42, 60, 60, "white"),
        ("GO GET IT -> 'Download Files' modal -> popup URL /dl/ token.", 26, 60, 125, "white"),
        ("raw curl: 403 - server mints tokens, session-bound only.", 24, 60, 162, "white"),
        ("Calls fetch WITH cookies, fulfills the popup, keeps the bytes.", 24, 60, 196, "white"),
    ]),
    (8, None, [
        ("5 - PORTALS & THE WALL", 50, 60, 60, "white"),
        ("portals virtual-render; server stops minting tokens at row 9", 28, 60, 150, "0xcfe6ff"),
        ("No Matching Records. Adaptive skip logs them; run12 pulled", 28, 60, 188, "0xcfe6ff"),
        ("10 of 43 Other Documents - the honest README lists the rest.", 28, 60, 226, "0xcfe6ff"),
    ]),
    (7, None, [
        ("6 - ZIP + REPLY", 50, 60, 60, "white"),
        ("ZIP: files + manifest.json + README (counts, refused rows).", 28, 60, 150, "0xcfe6ff"),
        ("reply: plain + HTML manifest table, ZIP attached, in-thread.", 26, 60, 190, "0xcfe6ff"),
    ]),
    (9, None, [
        ("WHAT I LEARNED", 50, 60, 60, "white"),
        ("probe the mechanism, not the markup: RPC payloads + viewport", 27, 60, 150, "0xcfe6ff"),
        ("matrix decoded the GWT portal (tall viewport -> 42 rows).", 27, 60, 187, "0xcfe6ff"),
        ("Lesson saved as a skill: filemaker-webdirect-scraping.", 27, 60, 224, "0xcfe6ff"),
        ("sourcecode: github.com/fortnbrnsecond1-maker/uarb-agent", 24, 60, 275, "0x9fe8c0"),
    ]),
]

# ffmpeg drawtext: a Windows font path needs the drive colon escaped and the whole
# filtergraph is built as ONE -vf string (no [v] labels), else 'Filter not found'.
FONT = "C\\:/Windows/Fonts/arialbd.ttf"

idx = 0
total = 0.0
for dur, img, texts in slides:
    base = [FF, "-y"]
    if img:
        base += ["-loop", "1", "-framerate", "10", "-t", str(dur), "-i", img]
    else:
        base += ["-f", "lavfi", "-i", f"color=c=0x0b1020:s=1600x900:d={dur}:r=10"]
    vf = ["scale=1600:900:force_original_aspect_ratio=decrease",
          "pad=1600:900:(ow-iw)/2:(oh-ih)/2:color=black"]
    for t, size, x, y, col in texts:
        esc = t.replace("'", "\\'").replace(":", "\\:")
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
