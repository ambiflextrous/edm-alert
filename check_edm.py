"""
EDM outage alert.

Scrapes https://www.edm.co.mz/manutencao, finds scheduled cuts
("Corte Programado") whose province matches PROVINCE, and emails
you about any outage reference code it hasn't alerted on before,
formatted in Portuguese similar to the site's own cards.

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

TAG_RE = re.compile(r"<[^>]+>")

WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

WEEKDAY_PT = {
    "Sunday": "Domingo", "Monday": "Segunda-feira", "Tuesday": "Terça-feira",
    "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira",
    "Saturday": "Sábado",
}
MONTH_PT = {
    "January": "Janeiro", "February": "Fevereiro", "March": "Março", "April": "Abril",
    "May": "Maio", "June": "Junho", "July": "Julho", "August": "Agosto",
    "September": "Setembro", "October": "Outubro", "November": "Novembro", "December": "Dezembro",
}

# Matches one full outage card in the order the site renders it:
# Weekday / day / Month Year / start / end / "Corte Programado" / CODE /
# Province / "ASC <office>" / "Bairros / Zonas Afectadas:" / affected areas
RECORD_RE = re.compile(
    r"(?P<weekday>" + "|".join(WEEKDAYS) + r")\s+"
    r"(?P<day>\d{1,2})\s+"
    r"(?P<month>" + "|".join(MONTHS) + r")\s+"
    r"(?P<year>\d{4})\s+"
    r"(?P<start>\d{1,2}:\d{2})\s+"
    r"(?P<end>\d{1,2}:\d{2})\s+"
    r"Corte Programado\s+"
    r"(?P<code>[A-Z]{3}\d{6}-\d{4})\s+"
    r"(?P<province>.+?)\s+"
    r"(?P<asc>ASC\s+\S+(?:[\s-]\S+)*?)\s+"
    r"Bairros\s*/\s*Zonas Afectadas:\s*"
    r"(?P<affected>.+?)"
    r"(?=(?:" + "|".join(WEEKDAYS) + r")|Adic\.\s*Alerta|$)",
    re.IGNORECASE | re.DOTALL,
)


def fetch_page_text() -> str:
    req = urllib.request.Request(
        URL, headers={"User-Agent": "Mozilla/5.0 (outage-alert script)"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
    text = TAG_RE.sub(" ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text)


def extract_outages(text: str) -> list[dict]:
    outages = []
    for m in RECORD_RE.finditer(text):
        d = m.groupdict()
        outages.append(
            {
                "code": d["code"],
                "province": d["province"].strip(),
                "asc": re.sub(r"\s+", " ", d["asc"]).strip(),
                "weekday": d["weekday"],
                "day": d["day"],
                "month": d["month"],
                "year": d["year"],
                "start": d["start"],
                "end": d["end"],
                "affected": d["affected"].strip().rstrip("."),
            }
        )
    return outages


def load_seen() -> set:
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text()))
    return set()


def save_seen(seen: set) -> None:
    STATE_FILE.write_text(json.dumps(sorted(seen), indent=2))


def format_time(t: str) -> str:
    h, m = t.split(":")
    return f"{int(h):02d}:{m}"


def format_outage_pt(o: dict) -> str:
    weekday_pt = WEEKDAY_PT.get(o["weekday"], o["weekday"])
    month_pt = MONTH_PT.get(o["month"], o["month"])
    return (
        f"CORTE DE ENERGIA — {o['province'].upper()}\n"
        f"{'-' * 40}\n"
        f"DATA DE CORTE: {o['day']} {month_pt.upper()} {o['year']}\n"
        f"DIA DA SEMANA DE CORTE: {weekday_pt.upper()}\n"
        f"INTERVALO DE CORTE: {format_time(o['start'])} - {format_time(o['end'])}\n"
        f"AGÊNCIA: {o['asc']}\n"
        f"CÓDIGO DE REFERÊNCIA: {o['code']}\n\n"
        f"ZONAS AFECTADAS:\n{o['affected']}."
    )


def send_email(new_outages: list[dict]) -> None:
    user = os.environ["SMTP_USER"]
    password = os.environ["SMTP_PASS"]
    to_addr = os.environ["ALERT_TO"]

    body_blocks = [format_outage_pt(o) for o in new_outages]
    body = f"\n\n{'=' * 40}\n\n".join(body_blocks)
    body += f"\n\nFonte: {URL}"

    msg = EmailMessage()
    msg["Subject"] = f"Corte de Energia: {PROVINCE}"
    msg["From"] = user
    msg["To"] = to_addr
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
        server.login(user, password)
        server.send_message(msg)


def main() -> int:
    text = fetch_page_text()
    outages = extract_outages(text)
    matching = [o for o in outages if PROVINCE.lower() in o["province"].lower()]

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
