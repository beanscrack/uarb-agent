"""TTS narration: 2-clip narration matching the 128s demo (see make_demo_final slides)."""
from textwrap import dedent

import edge_tts

VOICE = "en-US-AndrewMultilingualNeural"

PART1 = dedent("""\
    The UARB public documents agent is broken into components: an email front end,
    website navigation, document counting, document downloading, and zipping.
    Email in: the agent polls the mailbox, extracts a matter number and a document type,
    then starts a scrape.
    The site is a FileMaker WebDirect app. There's no REST API. The Matter field is a
    content editable, untrusted events are ignored. So the agent types with per character
    trusted key events, and validates the read back value before it clicks Search.
    The result tabs carry the doc counts, the body carries the matter metadata, this
    machine reads both from the live DOM.
""")

PART2 = dedent("""\
    Downloads are the hard part. Clicking Go Get It opens a Download Files modal, and
    its button opens a popup to a per row, server minted, token URL. Direct curl is a
    four zero three. The only working path: intercept the request in the browser
    session, with cookies, fulfill it, and keep the bytes.
    The server mints only about eight of those tokens per portal page: rows at, and
    past, the wall answer No Matching Records. The agent proves that, caps the harvest,
    and writes an honest manifest plus README that lists every refused row.
    The bundle is a zip with a manifest, replied in the email thread, as an HTML
    manifest table plus attachment, with a short summary of what the matter is.
    What I learned is all in the repo: probe the mechanism, not the markup.
""")


async def build():
    ok = True
    for name, text in (("narr1.mp3", PART1), ("narr2.mp3", PART2)):
        try:
            com = edge_tts.Communicate(" ".join(text.split()), VOICE, rate="-5%")
            await com.save(name)
            print("wrote", name)
        except Exception as e:
            ok = False
            print("edge tts failed:", e, "-> start the faceless narrator offline")
    return ok


if __name__ == "__main__":
    import asyncio

    asyncio.run(build())
