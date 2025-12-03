import re
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
import spacy
import dateparser
from fastapi.staticfiles import StaticFiles

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

app = FastAPI(title="CRM Data Filler - Prototype")

# Serve static UI
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory duplicate detection
in_memory_contacts = set()
in_memory_companies = set()


class ExtractRequest(BaseModel):
    meeting_text: str
    source: Optional[str] = "manual"


def parse_money_text(money_text: str):
    """
    Parse displayed money text to (value_number, currency_symbol)
    Handles patterns like: $30K, ₹30K, INR 12,00,000, 30K, 30k, 12,00,000
    """
    if not money_text:
        return None, None

    # Normalize
    s = money_text.replace(" ", "").replace("\u00A0", "")
    # currency symbol
    cur = None
    mcur = re.search(r'([₹$€£])', s)
    if mcur:
        cur = mcur.group(1)

    # Try numeric with multipliers
    m = re.search(r'([\d,]+(?:\.\d+)?)([KkLlcrCR]{0,2})', s)
    if m:
        num_str = m.group(1).replace(",", "")
        try:
            base = float(num_str)
        except:
            base = None
        mul = m.group(2).lower() if m.group(2) else ""
        if base is not None:
            if mul in ("k",):
                base = base * 1_000
            elif mul in ("l", "lk",):  # if someone writes L or l
                base = base * 100_000
            elif mul in ("cr",):
                base = base * 10_000_00  # 1 crore = 10,00,000
            # if no multiplier, base is actual number
            return base, cur
    # fallback: find large numeric like 1200000 with commas
    m2 = re.search(r'([\d,]{2,})', s)
    if m2:
        try:
            val = float(m2.group(1).replace(",", ""))
            return val, cur
        except:
            return None, cur

    return None, cur


def detect_stage(text: str):
    t = text.lower()
    if "demo" in t or "walk-through" in t or "walkthrough" in t or "product demo" in t:
        return "Demo Scheduled"
    if "poc" in t or "poC".lower() in t or "proof of concept" in t:
        return "PoC"
    if "proposal" in t or "quote" in t or "pricing" in t or "estimate" in t:
        return "Proposal"
    if "interested" in t or "evaluate" in t or "evaluating" in t:
        return "Qualified"
    return None


@app.post("/extract")
async def extract(req: ExtractRequest):
    text = req.meeting_text or ""
    doc = nlp(text)

    # ----------- BASIC EXTRACTION USING SPACY -----------
    persons = list({ent.text for ent in doc.ents if ent.label_ == "PERSON"})
    orgs = list({ent.text for ent in doc.ents if ent.label_ == "ORG"})
    gpes = list({ent.text for ent in doc.ents if ent.label_ in ("GPE", "LOC")})
    dates = list({ent.text for ent in doc.ents if ent.label_ in ("DATE", "TIME")})
    money = list({ent.text for ent in doc.ents if ent.label_ == "MONEY"})

    # ----------- TITLE HEURISTIC -----------
    title = None
    title_match = re.search(r"(Director|Manager|CTO|CEO|Lead|Head|VP|Founder|Officer)", text)
    if title_match:
        title = title_match.group(0)

    # ----------- EMAIL & PHONE EXTRACTION -----------
    email = None
    email_m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_m:
        email = email_m.group(0)

    phone = None
    phone_m = re.search(r"(\+\d{1,3}[-\s]?)?(\d{2,4}[-\s]?){1,4}\d{3,4}", text)
    if phone_m:
        phone = phone_m.group(0)

    # ----------- MONEY PARSING -----------
    value = None
    currency = None
    if money:
        # Use the first money entity and try parsing more robustly
        val, cur = parse_money_text(money[0])
        value = val
        currency = cur

    # If spaCy didn't find MONEY but text contains patterns like "30K" or "INR 12,00,000"
    if value is None:
        extra_money_match = re.search(r'((?:₹|INR|\$)?\s*[\d{1,3},]+[KkLlcrCR]*|\d+(?:\.\d+)?\s*[KkLlcrCR])', text)
        if extra_money_match:
            val, cur = parse_money_text(extra_money_match.group(0))
            value = val if value is None else value
            currency = currency or cur

    # ----------- DATE PARSING -----------
    parsed_dates = []
    for d in dates:
        p = dateparser.parse(d)
        if p:
            parsed_dates.append(p.date().isoformat())

    close_date = parsed_dates[0] if parsed_dates else None

    # ----------- CONTACT & COMPANY IDENTIFICATION -----------
    contact_name = persons[0] if persons else None
    company_name = orgs[0] if orgs else (gpes[0] if gpes else None)

    # ----------- PAIN POINTS -----------
    pain_points = []
    for sent in doc.sents:
        s = sent.text.lower()
        if any(k in s for k in ("need", "issue", "problem", "churn", "difficulty", "pain", "interested", "want", "looking for")):
            pain_points.append(sent.text.strip())

    # ----------- COMPETITORS -----------
    competitors = []
    competitor_matches = re.findall(r"(HubSpot|Salesforce|Zoho|Freshworks|Zendesk|Oracle)", text, re.I)
    competitors.extend(list({m for m in competitor_matches}))

    # ----------- NEXT ACTIONS -----------
    next_actions = []
    for sent in doc.sents:
        lower = sent.text.lower()
        if any(k in lower for k in ("next", "follow up", "demo", "schedule", "meeting", "follow-up")):
            due_date = None
            # Extract a date-like substring and parse
            d = re.search(r'([A-Z][a-z]+\s\d{1,2}(?:st|nd|rd|th)?(?:,?\s?\d{4})?)', sent.text)
            if d:
                parsed = dateparser.parse(d.group(0))
                if parsed:
                    due_date = parsed.date().isoformat()

            next_actions.append({
                "action": sent.text.strip(),
                "owner": "Sales Rep" if "sales" in lower or "rep" in lower else None,
                "due_date": due_date
            })

    # ----------- DEAL STAGE DETECTION -----------
    stage = detect_stage(text)

    # ----------- DUPLICATE DETECTION -----------
    contact_exists = email.lower() in in_memory_contacts if email else False
    company_exists = company_name.lower() in in_memory_companies if company_name else False

    if email:
        in_memory_contacts.add(email.lower())
    if company_name:
        in_memory_companies.add(company_name.lower())

    # ----------- FINAL STRUCTURED OUTPUT -----------
    extracted = {
        "contact": {
            "name": contact_name,
            "title": title,
            "email": email,
            "phone": phone
        },
        "company": {
            "name": company_name,
            "industry": None,
            "size": None,
            "website": None
        },
        "deal": {
            "name": f"{company_name or 'Opportunity'} Deal",
            "value_usd": value,
            "currency": currency,
            "stage": stage,
            "close_date": close_date
        },
        "pain_points": pain_points or None,
        "competitors": competitors or None,
        "next_actions": next_actions or None,
        "notes": text[:1000],
        "confidence": 0.80,
        "duplicate_checks": {
            "contact_exists": contact_exists,
            "company_exists": company_exists
        },
        "crm_push": {
            "status": "mocked",
            "contact_id": f"c-{int(datetime.now().timestamp())}",
            "company_id": f"co-{int(datetime.now().timestamp())}"
        }
    }

    # Return with agent-style message (matches PDF conversational flow)
    return {
        "agent_message": "Perfect! I've extracted and structured your CRM data:",
        "extracted": extracted
    }


@app.get("/")
def home():
    return {"message": "Go to /static/index.html to use the demo UI"}
