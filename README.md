# UARB Public-Docs Agent

Email in -> Nova Scotia UARB public documents -> ZIP reply.

The public database is a **FileMaker WebDirect** app (`https://uarb.novascotia.ca/fmi/webd/UARB15`):
a GWT/Vaadin canvas with no REST API, no normal DOM inputs, JavaScript-synthesized
events, per-IP server sessions, and download URLs that are **minted per row at click
time** (raw `curl` -> `403`). The agent drives a real browser session (Playwright) and
harvests files by intercepting the minted `/dl/` requests **in-session** (cookies
included) via a passthrough route.

## Layout

| file | role |
|---|---|
| `agent_mail.py` | email front-end: IMAP poll (allow-list + `seen.json` dedup, In-Reply-To threading) -> parse (Matter id + doc type) -> scrape -> ZIP + HTML-manifest reply with the ZIP attached |
| `uarb_scrape.py` | the scraper: search -> metadata/counts -> portal row walking -> `GO GET IT` -> modal -> download-token capture -> `manifest.json`, progress, README, ZIP |
| `probe_*.py` | ~35 calibration probes (kept deliberately): widget maps, RPC payload logs, portal mechanics (mechanism A-E), tall-viewport rendering, typing stress, row-9-wall research |
| `make_demo_final.py`, `capture_demo*.py`, `shot_reply.py` | demo video pipeline (ffmpeg slides + live evidence screenshots, rendered reply email) |

## Run

```bash
# scraper only (matter, doc type, output dir; optional row cap)
.venv/Scripts/python.exe uarb_scrape.py M12205 Exhibits out 13

# one-shot: scrape a matter and mail the bundle
.venv/Scripts/python.exe agent_mail.py test you@example.com M12205 "Key Documents"

# full agent (watch inbox)
.venv/Scripts/python.exe agent_mail.py watch 20
```

`.env` keys: `UARB_SMTP_HOST/PORT/USER/PASS`, `UARB_IMAP_HOST/PORT/USER/PASS`,
`AGENT_EMAIL`, optional `UARB_ALLOW_SENDERS`, `UARB_POLL_SECS`, `UARB_OUT_DIR`,
`UARB_SEEN_FILE`.

## The verified mechanics (what the probes proved)

- **Typing**: the Matter box is a `contenteditable` div (`#b0p0o254i0i0r1`, layout
  dependent); GWT ignores untrusted input. Per-character trusted key events, with
  read-back validation before Search (`#b0p0o258i0i0r1`).
- **Tabs/counts**: tab buttons carry the counts (`Exhibits - 13` ...) - read from the
  live DOM; metadata (type/status/title/dates/category) from the result body.
- **Portal rows**: rows are painted as aliased grid skins; row detection walks the
  DOM for leaf-text tokens (`GO GET IT` second-to-last, file extension last) under a
  ticket-cutoff guard (rows past the rendered `GO GET IT` count are ghosts - clicking
  one wedges the UI with a modal-less 'relationship' error; proved at row 9).
- **Downloads**: `GO GET IT` -> `Download Files` modal -> button opens a popup to a
  minted `/fmi/webd/APP/connector/{A}/{B}/dl/<doc>.<ext>` URL. Server mints
  per-row tokens bound to the session; **the only working retrieval is an in-context
  `route.fetch` (cookies) + `route.fulfill`, popup closed** (`probe_mechE2`: 8/8
  distinct PDFs, `%PDF`-checked).
- **The 8-row wall**: after 8 harvests the server answers `No Matching Records` for
  the next row in the page (proved: cold probe 2/13, mechE run 8/13, run12 10/43;
  tall viewport renders all rows yet rows >= 9 stay refused - a server-side, per
  session cap, not a DOM issue). Harvests cap at 8-10 per tab. Refusals are **logged
  honestly** in `manifest.json` + the ZIP README, not skipped silently.

Every input lane into the download (curl, exported cookies, RPC replay, counter
scanning with 488 cold tokens probed - all `403`/`204`) is in `probe_*`; direct paths
are impossible by design, so the agent rides the browser session.

## Demo video

`demo_uarb_agent.mp4` (~2 min) is assembled from the live evidence (real screenshots):
`python capture_demo.py && python capture_demo2.py && python shot_reply.py && python make_demo_final.py`.

## Notes

- Replies include a human summary built from the matter metadata (what it is, counts,
  dates, outcome) so the user knows what they are receiving - plus a manifest table.
- Reproducibility: `run*.log` and `out*/` artifacts are in-repo branch history in the
  submission package; probes kept on purpose - approach over polish.
