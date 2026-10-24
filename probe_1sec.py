"""Create/guess a 1secmail inbox, poll a few times, print messages as JSON."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

login = sys.argv[1] if len(sys.argv) > 1 else "uarb.agent.coop.test.7412"
dom = "1secmail.com"

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

# mailbox listing API
try:
    msgs = get(f"https://www.1secmail.com/api/v1/?action=getMessages&login={login}&domain={dom}")
    print("messages:", msgs)
except Exception as e:
    print("list err", e)

print("address:", f"{login}@{dom}")
