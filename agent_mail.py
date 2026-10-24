"""Email front-end for the UARB agent.

Wires: IMAP loop -> parse (matter, doc type) from the incoming email ->
scrape via uarb_scrape -> ZIP + summary email reply with attachment.

Credentials via .env (env vars): UARB_SMTP_HOST/PORT/USER/PASS,
UARB_IMAP_HOST/PORT/USER/PASS, AGENT_EMAIL (the address we monitor),
UARB_ALLOW_SENDERS (comma list, optional; empty = allow all).

Runs single-threaded: the UARB WebDirect session is per-IP, so requests are
served one at a time off the mail queue. Replies are sent in-thread
(In-Reply-To/References) with an HTML manifest and the ZIP attached.

Run:  python agent_mail.py watch [poll_secs]
      python agent_mail.py test <to> <matter> <doc type> [--dry]
      python agent_mail.py parse <subject> <body...>
"""
from __future__ import annotations

import email
import email.policy
import imaplib
import json
import os
import re
import smtplib
import sys
import time
from email.message import EmailMessage
from email.utils import make_msgid, parseaddr
from html import escape
from pathlib import Path

from dotenv import load_dotenv

from uarb_scrape import scrape  # noqa: E402

load_dotenv()

OUT = Path(os.environ.get("UARB_OUT_DIR", Path(__file__).resolve().parent / "out_mail"))
MATTER_RE = re.compile(r"\bM\d{5}\b", re.I)
DOC_TYPES = ["key documents", "other documents", "exhibits", "transcripts", "recordings"]
SEEN_FILE = Path(os.environ.get("UARB_SEEN_FILE", str(Path(__file__).resolve().parent / "seen.json")))
_SEEN: set[str] = set()


def _seen_load() -> None:
    global _SEEN
    if SEEN_FILE.exists():
        try:
            _SEEN = set(json.loads(SEEN_FILE.read_text()))
        except Exception:  # noqa: BLE001
            pass


def _seen_add(mid: str) -> None:
    _SEEN.add(mid)
    tmp = SEEN_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(sorted(_SEEN)))
    tmp.replace(SEEN_FILE)


def parse_request(subject: str, body: str):
    text = f"{subject}\n{body}"
    m = MATTER_RE.search(text)
    if not m:
        return None
    matter = m.group(0).upper()
    low = text.lower()
    # longest phrase first so "key documents" wins over "documents"
    for dt in sorted(DOC_TYPES, key=len, reverse=True):
        if dt in low:
            return matter, dt.title()
    return matter, None


def _imap_login():
    host = os.environ["UARB_IMAP_HOST"]
    user = os.environ["UARB_IMAP_USER"]
    pw = os.environ["UARB_IMAP_PASS"]
    box = os.environ.get("UARB_IMAP_BOX", "INBOX")
    imap = imaplib.IMAP4_SSL(host, int(os.environ.get("UARB_IMAP_PORT", "993")))
    imap.login(user, pw)
    imap.select(box)
    return imap


def fetch_new_emails(imap):
    items = []
    typ, data = imap.search(None, "UNSEEN")
    ids = data[0].split() if data and data[0] else []
    for num in ids:
        typ, msgdata = imap.fetch(num, "(BODY.PEEK[])")
        raw = msgdata[0][1]
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        subj = msg.get("Subject", "")
        sender = msg.get("From", "")
        mid = (msg.get("Message-ID") or "").strip()
        refs = (msg.get("References") or msg.get("In-Reply-To") or "").strip()
        try:
            body = msg.get_body(preferencelist=("plain", "html"))
            body_txt = body.get_content() if body else ""
        except Exception:  # noqa: BLE001
            body_txt = ""
        items.append((num, sender, subj, body_txt, mid, refs))
    return items


def mark_seen(imap, imap_num) -> None:
    imap.store(imap_num, "+FLAGS", "\\Seen")


def build_reply_meta(meta: dict, tab: str, files: list[dict]) -> str:
    counts = meta.get("counts", {})
    total = sum(counts.values())
    parts = []
    title = meta.get("title")
    if title:
        parts.append(f"{meta.get('matter')} is about: {title}.")
    bits = [f"It relates to {meta.get('type')}" if meta.get("type") else "",
            f"within the {meta.get('category')} category." if meta.get("category") else ""]
    if meta.get("type"):
        parts.append(" ".join(b for b in bits if b))
    dates = []
    if meta.get("date_opened"):
        dates.append(f"initial filing on {_fmt(meta['date_opened'])}")
    if meta.get("date_final"):
        dates.append(f"final filing on {_fmt(meta['date_final'])}")
    if dates:
        parts.append("The matter had an " + " and ".join(dates) + ".")
    found = ", ".join(f"{v} {k}" for k, v in counts.items())
    parts.append(f"It has {total} documents in total: {found}.")
    parts.append(f"I found {len(files)} {tab} and I am attaching them as a ZIP.")
    want = counts.get(tab, 0)
    if want > len(files):
        parts.append(
            f"Note: {want - len(files)} of the {tab} offered no download token in FileMaker "
            "WebDirect ('No Matching Records'); they are listed in the README inside the ZIP."
        )
    return "\n\n".join(parts)


def _fmt(d: str) -> str:
    try:
        mth, day, yr = d.split("/")
        import calendar

        return f"{calendar.month_abbr[int(mth)]} {int(day)}, {yr}"
    except Exception:  # noqa: BLE001
        return d


def build_bundle_html(meta: dict, files: list[dict], matter: str, tab: str) -> str:
    rows = "".join(
        f"<tr><td>{escape(str(f.get('doc','')))}</td><td>{escape(str(f.get('title') or ''))}</td>"
        f"<td>{escape(str(f.get('date') or ''))}</td><td>{int(f.get('bytes',0))//1024} KiB</td></tr>"
        for f in files
    )
    counts = meta.get("counts") or {}
    return (
        f"<html><body style='font-family:Arial,sans-serif'>"
        f"<h3>UARB {escape(matter)} — {escape(tab)} bundle ({len(files)} files)</h3>"
        f"<p style='color:#555'>{escape(str(meta.get('type') or ''))} · {escape(str(meta.get('status') or ''))} · "
        f"{escape(str(meta.get('title') or '')[:140])}</p>"
        f"<p>Document counts: {', '.join(f'{k}: {v}' for k, v in counts.items())}</p>"
        f"<table border='1' cellpadding='6' style='border-collapse:collapse;font-size:13px'>"
        f"<tr style='background:#eef'><th>Doc #</th><th>Title</th><th>Date</th><th>Size</th></tr>{rows}</table>"
        f"<p style='color:#777;font-size:12px'>ZIP attached. Source: github.com/fortnbrnsecond1-maker/uarb-agent</p>"
        f"</body></html>"
    )


def send_zip(to_addr: str, subject: str, text: str, zip_path: Path | None, html: str | None = None,
             in_reply_to: str = "") -> None:
    host = os.environ["UARB_SMTP_HOST"]
    port = int(os.environ.get("UARB_SMTP_PORT", "587"))
    user = os.environ["UARB_SMTP_USER"]
    pw = os.environ["UARB_SMTP_PASS"]
    use_ssl = os.environ.get("UARB_SMTP_SSL", "0") == "1"
    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg["Message-ID"] = make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(text)
    if html:
        msg.add_alternative(html, subtype="html")
    if zip_path and Path(zip_path).exists():
        msg.add_attachment(
            Path(zip_path).read_bytes(),
            maintype="application",
            subtype="zip",
            filename=Path(zip_path).name,
        )
    if use_ssl:
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(user, pw)
            s.send_message(msg)
    else:
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, pw)
            s.send_message(msg)
    extra = f" ({Path(zip_path).name}, {Path(zip_path).stat().st_size} bytes)" if zip_path and Path(zip_path).exists() else ""
    print(f"sent to {to_addr} via {host}:{port}{extra}")


def handle(sender: str, subject: str, body: str, dry_send: bool = False, in_reply_to: str = "") -> bool:
    req = parse_request(subject, body)
    if not req:
        return False
    matter, doc = req
    if not doc:
        text = (
            "Hi, I couldn't tell which document type you want. "
            "Please ask for one of: Exhibits, Key Documents, Other Documents, Transcripts, Recordings. "
            "(Example: 'Other Documents files from M12205')"
        )
        if dry_send:
            print("DRY:", text)
        else:
            send_zip(sender, f"Re: {subject}", text, None, in_reply_to=in_reply_to)
        return True
    matter = matter.upper()
    print(f"[agent] request {matter} / {doc} from {sender}")
    st = scrape(matter, doc, OUT)
    files = st.get("files", [])
    meta = st.get("meta", {})
    zpath = Path(st.get("zip") or "")
    summary = build_reply_meta(meta, doc, files)
    html = build_bundle_html(meta, files, matter, doc)
    if dry_send:
        print("DRY subject:", f"UARB {matter} {doc} - {len(files)} files")
        print(summary)
        print("zip:", zpath)
    else:
        subj = (f"Re: {subject} - {len(files)} {doc} files" if subject.lower().startswith("re:")
                else f"UARB {matter} {doc} - {len(files)} files")
        send_zip(sender, subj, summary, zpath, html, in_reply_to=in_reply_to)
    return True


def watch(poll_secs: int = 20) -> None:
    _seen_load()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"[agent] watching INBOX every {poll_secs}s (Ctrl-C to stop)")
    imap = None
    while True:
        try:
            if imap is None:
                imap = _imap_login()
            for num, sender, subj, body, mid, refs in fetch_new_emails(imap):
                addr = parseaddr(sender)[1].lower()
                allow = [a.strip().lower() for a in os.environ.get("UARB_ALLOW_SENDERS", "").split(",") if a.strip()]
                agent = os.environ.get("AGENT_EMAIL", "").lower()
                if (mid and mid in _SEEN) or addr == agent:
                    mark_seen(imap, num)
                    continue
                if allow and addr not in allow:
                    mark_seen(imap, num)
                    continue
                try:
                    handle(addr, subj, body, in_reply_to=mid)
                finally:
                    mark_seen(imap, num)
                    if mid:
                        _seen_add(mid)
            imap.noop()
        except KeyboardInterrupt:
            raise
        except Exception as e:  # noqa: BLE001
            print("[agent] loop error:", e)
            try:
                if imap:
                    imap.logout()
            except Exception:  # noqa: BLE001
                pass
            imap = None
        time.sleep(poll_secs)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    if cmd == "watch":
        watch(int(sys.argv[2]) if len(sys.argv) > 2 else 20)
    elif cmd == "parse":
        print(parse_request(sys.argv[2], " ".join(sys.argv[3:])))
    elif cmd == "test":
        # test <to> <matter> <doc type> [--dry]
        to = sys.argv[2]
        matter = sys.argv[3]
        doc = sys.argv[4]
        dry = "--dry" in sys.argv
        body = f"agent, please give me {doc} for {matter}"
        ok = handle(to, f"docs {matter}", body, dry_send=dry)
        print("handled:", ok)
    else:
        print(__doc__)
