"""Generate sample ticket data files under samples/ and validate them."""

import csv
import json
import random
from pathlib import Path
from xml.etree import ElementTree as ET

from app.parsers import parse_file
from app.schemas import TicketCreate

ROOT = Path.cwd()
assert (ROOT / "pyproject.toml").exists(), "run from the project root"
SAMPLES = ROOT / "samples"
INVALID = SAMPLES / "invalid"
SAMPLES.mkdir(exist_ok=True)
INVALID.mkdir(exist_ok=True)

random.seed(42)

FIRST = ["Olena", "Ivan", "Petro", "Ann", "Marta", "Dmytro", "Sofia", "Roman",
         "Kate", "Taras", "Nina", "Yurii", "Lesia", "Mark", "Iryna", "Oleg"]
LAST = ["Shevchenko", "Kovalenko", "Bondar", "Tkachuk", "Melnyk", "Kravets",
        "Boyko", "Lysenko", "Ponomarenko", "Savchenko"]

# (subject, description, category) — keywords intentionally align with the classifier
TOPICS = [
    ("Can't log into my account",
     "After the last password reset my login attempts fail with an authentication error.",
     "account_access"),
    ("2FA code never arrives",
     "The two-factor verification code is not delivered to my phone, I am locked out.",
     "account_access"),
    ("Account locked after vacation",
     "My account locked message appears every time I try to sign in with valid credentials.",
     "account_access"),
    ("Session expires too fast",
     "The session expired notice appears after two minutes and forces me to log in again.",
     "account_access"),
    ("Dashboard shows an error",
     "The analytics dashboard shows a timeout error and sometimes crashes during load.",
     "technical_issue"),
    ("Export to PDF not working",
     "Exporting reports fails with an exception, the button simply does not work anymore.",
     "technical_issue"),
    ("Page freezes on save",
     "The editor freezes when I press save and the browser tab becomes unresponsive.",
     "technical_issue"),
    ("Sync is very slow",
     "Synchronization between devices is slow and often ends with a timeout failure.",
     "technical_issue"),
    ("Charged twice this month",
     "My invoice shows a double charge for the same subscription period, I need a refund.",
     "billing_question"),
    ("Question about renewal price",
     "The renewal pricing on my latest receipt differs from the plan I originally bought.",
     "billing_question"),
    ("Refund still not received",
     "I cancelled two weeks ago and the promised refund has not reached my credit card.",
     "billing_question"),
    ("Update payment method",
     "I need to change the credit card used for billing before the next payment date.",
     "billing_question"),
    ("Please add dark mode",
     "It would be nice to add support for a dark theme, this is just a suggestion.",
     "feature_request"),
    ("Feature request: CSV export",
     "An enhancement idea: please add an export of the ticket list to CSV files.",
     "feature_request"),
    ("Improvement for search",
     "I suggest an improvement so search understands partial matches and typos better.",
     "feature_request"),
    ("Crash when uploading avatar",
     "Steps to reproduce:\n1. Open profile\n2. Upload a PNG avatar\nExpected behavior: image saves. Actual behavior: the app crashes with an error.",
     "bug_report"),
    ("Wrong totals in report",
     "Steps to reproduce:\n1. Create two invoices\n2. Open the monthly report\nExpected result: totals match. Actual result: the regression shows doubled numbers.",
     "bug_report"),
    ("Broken link in welcome email",
     "The getting started link returns a 404 page, reproduction is stable on every send.",
     "bug_report"),
    ("General question about limits",
     "Where can I read about plan limits and how many seats my team can use in total?",
     "other"),
    ("Thanks for the great support",
     "Just wanted to leave positive feedback about the recent onboarding experience.",
     "other"),
]

PRIORITIES = ["urgent", "high", "medium", "medium", "medium", "low"]
STATUSES = ["new", "new", "new", "in_progress", "waiting_customer", "resolved", "closed"]
SOURCES = ["web_form", "email", "api", "chat", "phone"]
BROWSERS = ["Chrome 126", "Firefox 127", "Safari 18", "Edge 125", ""]
DEVICES = ["desktop", "mobile", "tablet", ""]
TAG_POOL = {
    "account_access": ["login", "password", "2fa", "access"],
    "technical_issue": ["error", "crash", "performance", "sync"],
    "billing_question": ["billing", "invoice", "refund", "payment"],
    "feature_request": ["enhancement", "ui", "export", "idea"],
    "bug_report": ["bug", "regression", "crash", "repro"],
    "other": ["question", "feedback"],
}
AGENTS = ["agent.olha", "agent.smith", "agent.kova", ""]


def make_ticket(n: int) -> dict:
    subject, description, category = TOPICS[n % len(TOPICS)]
    name = f"{random.choice(FIRST)} {random.choice(LAST)}"
    tags = random.sample(TAG_POOL[category], k=random.randint(0, 2))
    source = random.choice(SOURCES)
    metadata = {"source": source}
    browser = random.choice(BROWSERS)
    device = random.choice(DEVICES)
    if browser:
        metadata["browser"] = browser
    if device:
        metadata["device_type"] = device
    ticket = {
        "customer_id": f"CUST-{1000 + n}",
        "customer_email": f"{name.split()[0].lower()}.{name.split()[1].lower()}{n}@example.com",
        "customer_name": name,
        "subject": subject,
        "description": description,
        "category": category,
        "priority": random.choice(PRIORITIES),
        "status": random.choice(STATUSES),
        "tags": tags,
        "metadata": metadata,
    }
    assigned = random.choice(AGENTS)
    if assigned:
        ticket["assigned_to"] = assigned
    return ticket


CSV_FIELDS = ["customer_id", "customer_email", "customer_name", "subject", "description",
              "category", "priority", "status", "assigned_to", "tags",
              "source", "browser", "device_type"]


def csv_row(ticket: dict) -> dict:
    row = {f: ticket.get(f, "") for f in CSV_FIELDS}
    row["tags"] = ";".join(ticket.get("tags", []))
    meta = ticket.get("metadata", {})
    row["source"] = meta.get("source", "")
    row["browser"] = meta.get("browser", "")
    row["device_type"] = meta.get("device_type", "")
    return row


def write_csv(path: Path, tickets: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(csv_row(t) for t in tickets)


def write_xml(path: Path, tickets: list[dict]) -> None:
    root = ET.Element("tickets")
    for ticket in tickets:
        el = ET.SubElement(root, "ticket")
        for key in ("customer_id", "customer_email", "customer_name", "subject",
                    "description", "category", "priority", "status", "assigned_to"):
            if ticket.get(key):
                ET.SubElement(el, key).text = str(ticket[key])
        if ticket.get("tags"):
            tags_el = ET.SubElement(el, "tags")
            for tag in ticket["tags"]:
                ET.SubElement(tags_el, "tag").text = tag
        meta_el = ET.SubElement(el, "metadata")
        for key, value in ticket["metadata"].items():
            ET.SubElement(meta_el, key).text = value
    ET.indent(root)
    path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n")


# ----- valid samples ---------------------------------------------------------
csv_tickets = [make_ticket(n) for n in range(50)]
json_tickets = [make_ticket(50 + n) for n in range(20)]
xml_tickets = [make_ticket(70 + n) for n in range(30)]

write_csv(SAMPLES / "sample_tickets.csv", csv_tickets)
(SAMPLES / "sample_tickets.json").write_text(json.dumps(json_tickets, indent=2) + "\n")
write_xml(SAMPLES / "sample_tickets.xml", xml_tickets)

# ----- invalid samples for negative tests ------------------------------------
# CSV: 2 valid rows + 4 broken ones (bad email, short description, bad enums,
# subject too long / missing required field)
bad_csv = [csv_row(make_ticket(200)), csv_row(make_ticket(201))]
r = csv_row(make_ticket(202)); r["customer_email"] = "not-an-email"; bad_csv.append(r)
r = csv_row(make_ticket(203)); r["description"] = "too short"; bad_csv.append(r)
r = csv_row(make_ticket(204)); r["category"] = "nonsense"; r["priority"] = "mega"; bad_csv.append(r)
r = csv_row(make_ticket(205)); r["subject"] = "X" * 250; r["customer_name"] = ""; bad_csv.append(r)
with (INVALID / "invalid_tickets.csv").open("w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerows(bad_csv)

# JSON: 1 valid + invalid email, bad status, missing fields, non-object item
bad_json = [
    make_ticket(210),
    dict(make_ticket(211), customer_email="broken-at-example.com"),
    dict(make_ticket(212), status="sleeping", priority="whenever"),
    {"customer_id": "CUST-999", "subject": "Missing almost everything"},
    "just a string, not a ticket object",
]
(INVALID / "invalid_tickets.json").write_text(json.dumps(bad_json, indent=2, default=str) + "\n")

# XML: 1 valid + invalid email + bad device_type + description too short
t_ok, t_bad1, t_bad2, t_bad3 = make_ticket(220), make_ticket(221), make_ticket(222), make_ticket(223)
t_bad1["customer_email"] = "no-at-sign"
t_bad2["metadata"] = {"source": "telepathy", "device_type": "fridge"}
t_bad3["description"] = "short"
write_xml(INVALID / "invalid_tickets.xml", [t_ok, t_bad1, t_bad2, t_bad3])

# structurally broken files
(INVALID / "malformed.json").write_text('[{"customer_id": "CUST-1",\n')
(INVALID / "malformed.xml").write_text("<tickets><ticket><subject>never closed\n")
(INVALID / "empty.csv").write_text("")
(INVALID / "not_utf8.csv").write_bytes(b"\xff\xfe\x00 broken bytes")
(INVALID / "unsupported.txt").write_text("plain text, not an importable format\n")

# ----- validate everything through the real parsers/schema -------------------
def count_valid(path: Path, fmt: str) -> tuple[int, int]:
    records = parse_file(path.read_bytes(), fmt)
    ok = bad = 0
    for record in records:
        try:
            TicketCreate.model_validate(record)
            ok += 1
        except Exception:
            bad += 1
    return ok, bad


for path, fmt, want_ok, want_bad in [
    (SAMPLES / "sample_tickets.csv", "csv", 50, 0),
    (SAMPLES / "sample_tickets.json", "json", 20, 0),
    (SAMPLES / "sample_tickets.xml", "xml", 30, 0),
    (INVALID / "invalid_tickets.csv", "csv", 2, 4),
    (INVALID / "invalid_tickets.json", "json", 1, 4),
    (INVALID / "invalid_tickets.xml", "xml", 1, 3),
]:
    ok, bad = count_valid(path, fmt)
    status = "OK " if (ok, bad) == (want_ok, want_bad) else "FAIL"
    print(f"{status} {path.relative_to(ROOT)}: valid={ok} invalid={bad} (expected {want_ok}/{want_bad})")
