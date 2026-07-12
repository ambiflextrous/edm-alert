"""
EDM outage alert for Cabo Delgado.

Scrapes https://www.edm.co.mz/manutencao, finds scheduled cuts
("Corte Programado") whose province matches PROVINCE, and emails
you about any outage reference code it hasn't alerted on before.

State (already-alerted codes) is kept in seen_ids.json, which the
GitHub Actions workflow commits back to the repo.

Required environment variables (set as GitHub Secrets):
  SMTP_USER  - Gmail address used to send the alert
  SMTP_PASS  - Gmail App Password (not your normal password)
  ALERT_TO   - destination email (can be the same address)
Optional:
  PROVINCE   - defaults to "Cabo Delgado"
"""

import html
import json
import os
import re
import smtplib
import ssl
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

URL = "https://www.edm.co.mz/manutencao"
PROVINCE = os.environ.get("PROVINCE", "Cabo Delgado")
STATE_FILE = Path(__file__).parent / "seen_ids.json"

# Outage reference codes look like PEM260705-0092
CODE_RE = re.compile(r"\b([A-Z]{3}\d{6}-\d{4})\b")
TAG_RE = re.compile(r"<[^>]+>")


def fetch_page_text() -> str:
    req = urllib.request.Request(
        URL, headers={"User-Agent": "Mozilla/5.0 (outage-alert script)"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    # Strip tags, unescape entities, collapse whitespace
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


def extract_outages(text: str) -> list[dict]:
    """Split page text into blocks around each reference code."""
    outages = []
    matches = list(CODE_RE.finditer(text))
    for i, m in enumerate(matches):
        code = m.group(1)
        # Province and affected areas appear AFTER the code on this page.
        # Only look at text between this code and the next one, so stray
        # mentions (e.g. the province filter dropdown) can't false-match.
        end = matches[i + 1].start() if i + 1 < len(matches) else m.end() + 600
        block = text[m.start():end]
        outages.append({"code": code, "block": block.strip()})
    return outages


def load_seen() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set) -> None:
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=2))


def send_email(new_outages: list[dict]) -> None:
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    to_addr = os.environ["ALERT_TO"]

    lines = [f"New scheduled power cut(s) announced for {PROVINCE}:\n"]
    for o in new_outages:
        lines.append(f"Reference: {o['code']}")
        lines.append(f"Details: {o['block']}")
        lines.append("-" * 60)
    lines.append(f"\nSource: {URL}")

    msg = EmailMessage()
    msg["Subject"] = f"⚡ EDM: {len(new_outages)} power cut(s) scheduled — {PROVINCE}"
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content("\n".join(lines))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(user, password)
        server.send_message(msg)


def main() -> int:
    text = fetch_page_text()
    outages = extract_outages(text)
    matching = [o for o in outages if PROVINCE.lower() in o["block"].lower()]

    seen = load_seen()
    new = [o for o in matching if o["code"] not in seen]

    print(f"Found {len(outages)} total outages, "
          f"{len(matching)} in {PROVINCE}, {len(new)} new.")

    if new:
        send_email(new)
        seen.update(o["code"] for o in new)
        save_seen(seen)
        print("Alert email sent:", ", ".join(o["code"] for o in new))
    else:
        print("Nothing new — no email sent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
