"""Detectors for Indian personal data.

Each detector looks at two things: the column name (a hint) and a sample of
values. Some identifiers are strong on their own (an email address, a PAN, a
valid Aadhaar checksum). Others are just numbers or words, so they only count
when the column name points the same way (a bank account number, a name).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Verhoeff checksum, used by Aadhaar numbers
# ---------------------------------------------------------------------------

_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_valid(number: str) -> bool:
    """True if the digit string passes the Verhoeff check."""
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(number: str) -> str:
    """Check digit to append to a digit string (used to build test data)."""
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


# ---------------------------------------------------------------------------
# Value tests
# ---------------------------------------------------------------------------

_SEP = re.compile(r"[\s\-]")

AADHAAR_RE = re.compile(r"^[2-9]\d{11}$")
TWELVE_DIGITS_RE = re.compile(r"^\d{12}$")
PAN_RE = re.compile(r"^[A-Z]{3}[PCHFATBLJG][A-Z]\d{4}[A-Z]$")
IFSC_RE = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")
EMAIL_RE = re.compile(r"^[\w.+\-]+@[\w\-]+(\.[\w\-]+)+$")
PHONE_RE = re.compile(r"^(?:\+?91|0)?[6-9]\d{9}$")
ACCOUNT_RE = re.compile(r"^\d{9,18}$")
PINCODE_RE = re.compile(r"^[1-9]\d{5}$")
NAME_CHARS_RE = re.compile(r"^[A-Za-z઀-૿ऀ-ॿ .'\-]{2,60}$")
NUMBER_RE = re.compile(r"^\d+(\.\d+)?$")

CATEGORY_VALUES = {
    "GEN", "GENERAL", "OPEN", "UR", "OBC", "SC", "ST", "EWS", "SEBC", "NT", "DNT", "VJNT", "SBC",
}
GENDER_VALUES = {"M", "F", "MALE", "FEMALE", "OTHER", "O", "T", "TRANSGENDER"}
DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d")


def _digits(v: str) -> str:
    return _SEP.sub("", v)


def is_aadhaar(v: str) -> bool:
    d = _digits(v)
    return bool(AADHAAR_RE.match(d)) and verhoeff_valid(d)


def is_twelve_digits(v: str) -> bool:
    return bool(TWELVE_DIGITS_RE.match(_digits(v)))


def is_pan(v: str) -> bool:
    return bool(PAN_RE.match(v.strip().upper()))


def is_ifsc(v: str) -> bool:
    return bool(IFSC_RE.match(v.strip().upper()))


def is_email(v: str) -> bool:
    return bool(EMAIL_RE.match(v.strip()))


def is_phone(v: str) -> bool:
    return bool(PHONE_RE.match(_digits(v).lstrip("+")))


def is_account(v: str) -> bool:
    return bool(ACCOUNT_RE.match(_digits(v)))


def is_pincode(v: str) -> bool:
    return bool(PINCODE_RE.match(v.strip()))


def is_name(v: str) -> bool:
    v = v.strip()
    return bool(NAME_CHARS_RE.match(v)) and any(ch.isalpha() for ch in v)


def is_category(v: str) -> bool:
    return v.strip().upper() in CATEGORY_VALUES


def is_gender(v: str) -> bool:
    return v.strip().upper() in GENDER_VALUES


def is_number(v: str) -> bool:
    return bool(NUMBER_RE.match(v.strip().replace(",", "")))


def is_text(v: str) -> bool:
    return len(v.strip()) > 0


def parse_date(v: str) -> Optional[date]:
    v = v.strip()[:10]
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(v, fmt).date()
        except ValueError:
            continue
    return None


def is_date(v: str) -> bool:
    return parse_date(v) is not None


def age_on(born: date, today: date) -> int:
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


# ---------------------------------------------------------------------------
# Masking: reports never show raw values
# ---------------------------------------------------------------------------


def mask_keep_last4(v: str) -> str:
    v = v.strip()
    alnum = [i for i, ch in enumerate(v) if ch.isalnum()]
    keep = set(alnum[-4:])
    return "".join(ch if (i in keep or not ch.isalnum()) else "X" for i, ch in enumerate(v))


def mask_email(v: str) -> str:
    local, _, domain = v.strip().partition("@")
    return (local[:1] + "***@" + domain) if domain else "***"


def mask_name(v: str) -> str:
    parts = [p for p in v.strip().split() if p]
    return " ".join(p[0] + "." for p in parts) if parts else "***"


def mask_date(v: str) -> str:
    d = parse_date(v)
    return f"XX-XX-{d.year}" if d else "XX-XX-XXXX"


def mask_all(v: str) -> str:
    return "[hidden]"


# ---------------------------------------------------------------------------
# Detector catalogue
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Detector:
    id: str
    label: str
    group: str  # identity, contact, financial, sensitive, personal
    test: Callable[[str], bool]
    hint: re.Pattern
    needs_hint: bool  # value test alone is too weak to trust
    hint_only_ok: bool  # column name alone is enough (free-form values)
    mask: Callable[[str], str]
    note: str
    sensitive: bool = False


def _h(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


# Column names that contain "name" but are not about a person.
NOT_PERSON_NAME = _h(
    r"(subject|course|scheme|file|dept|department|college|institute|bank|branch|program|"
    r"programme|user\s?name|host|table|column|event|book|item|product|company|school|board|"
    r"hostel|block|room|exam)\s?name|^name\s?of\s?(scheme|course)"
)

DETECTORS: list[Detector] = [
    Detector(
        "aadhaar", "Aadhaar number", "identity", is_aadhaar,
        _h(r"aadh?aa?r|\buid\b|uidai|આધાર|आधार"), needs_hint=False, hint_only_ok=False,
        mask=mask_keep_last4,
        note="Keep only if a rule requires it. Store the masked form (last 4 digits) wherever possible.",
        sensitive=True,
    ),
    Detector(
        "apaar", "APAAR / ABC ID", "identity", is_twelve_digits,
        _h(r"apaar|\babc\b|abc\s?id|academic\s?bank"), needs_hint=True, hint_only_ok=False,
        mask=mask_keep_last4,
        note="Lifelong academic ID linked to Aadhaar. Limit who can see it.",
    ),
    Detector(
        "pan", "PAN", "identity", is_pan,
        _h(r"\bpan\b|pan\s?(no|number|card)|permanent\s?account"), needs_hint=False, hint_only_ok=False,
        mask=mask_keep_last4,
        note="Usually needed only for salary and TDS. Restrict to accounts staff.",
    ),
    Detector(
        "phone", "Mobile number", "contact", is_phone,
        _h(r"mobile|phone|contact|whatsapp|\bmob\b|cell|મોબાઇલ|મોબાઈલ|ફોન|मोबाइल|फ़ोन|फोन"), needs_hint=False, hint_only_ok=False,
        mask=mask_keep_last4,
        note="Contact data. Use it only for the purpose it was collected for.",
    ),
    Detector(
        "email", "Email address", "contact", is_email,
        _h(r"e\s?mail|mail\s?id|ઈમેલ|ઇમેલ|ईमेल"), needs_hint=False, hint_only_ok=False,
        mask=mask_email,
        note="Contact data. Use it only for the purpose it was collected for.",
    ),
    Detector(
        "ifsc", "IFSC code", "financial", is_ifsc,
        _h(r"ifsc"), needs_hint=False, hint_only_ok=False,
        mask=mask_all,
        note="Not personal on its own, but marks this table as holding bank details.",
    ),
    Detector(
        "bank_account", "Bank account number", "financial", is_account,
        _h(r"(bank|acc(oun)?t|\ba\s?c\b)(\s?(no|num|number))?|ખાતા|बैंक|खाता"), needs_hint=True, hint_only_ok=False,
        mask=mask_keep_last4,
        note="Financial data. Restrict access and delete once payments are settled.",
        sensitive=True,
    ),
    Detector(
        "dob", "Date of birth", "personal", is_date,
        _h(r"\bdob\b|birth|b\s?date|date\s?of\s?birth|જન્મ|जन्म"), needs_hint=True, hint_only_ok=False,
        mask=mask_date,
        note="Shows age. Records of anyone under 18 need verifiable parental consent under DPDP.",
    ),
    Detector(
        "caste", "Caste / category", "sensitive", is_category,
        _h(r"caste|category|community|reservation|quota|\bcat\b|જાતિ|જ્ઞાતિ|કેટેગરી|जाति|श्रेणी"), needs_hint=False, hint_only_ok=True,
        mask=mask_all,
        note="Highly sensitive. Keep it only where reservation or scholarship rules need it, with tight access.",
        sensitive=True,
    ),
    Detector(
        "income", "Family income", "financial", is_number,
        _h(r"income|salary\s?of\s?parent|annual\s?income"), needs_hint=True, hint_only_ok=True,
        mask=mask_all,
        note="Financial data about the family. Restrict to the scholarship cell.",
        sensitive=True,
    ),
    Detector(
        "disability", "Disability status", "sensitive", is_text,
        _h(r"disab|\bpwd\b|divyang|handicap|special\s?needs"), needs_hint=True, hint_only_ok=True,
        mask=mask_all,
        note="Health-related and highly sensitive. Restrict to the people who need it.",
        sensitive=True,
    ),
    Detector(
        "gender", "Gender", "personal", is_gender,
        _h(r"gender|\bsex\b"), needs_hint=True, hint_only_ok=True,
        mask=mask_all,
        note="Personal data. Collect it only where it is needed.",
    ),
    Detector(
        "address", "Address", "personal", is_text,
        _h(r"address|addr|street|locality|residence|સરનામું|सरनामु|पता"), needs_hint=True, hint_only_ok=True,
        mask=mask_all,
        note="Home address. Limit who can see it.",
    ),
    Detector(
        "pincode", "PIN code", "personal", is_pincode,
        _h(r"pin\s?code|\bpin\b|postal|zip"), needs_hint=True, hint_only_ok=False,
        mask=mask_all,
        note="Part of an address. Fine on its own, sensitive next to a name.",
    ),
    Detector(
        "person_name", "Person's name", "personal", is_name,
        _h(r"name|guardian|father|mother|parent|^(student|candidate|applicant|employee|staff|faculty)$|નામ|પિતા|માતા|नाम|पिता|माता"), needs_hint=True, hint_only_ok=False,
        mask=mask_name,
        note="Names make every other field in the row personal data.",
    ),
    Detector(
        "student_id", "Student / staff ID", "identity", is_text,
        _h(r"enrol+(ment)?|roll\s?no|reg(istration)?\s?no|student\s?id|emp(loyee)?\s?(id|code|no)|\bprn\b|gr\s?no"),
        needs_hint=True, hint_only_ok=True,
        mask=mask_keep_last4,
        note="Internal ID. Personal data because it points to one person.",
    ),
]

DETECTORS_BY_ID = {d.id: d for d in DETECTORS}

# Patterns searched inside free text (remarks, notes, comments).
EMBEDDED = {
    "phone": re.compile(r"(?<!\d)(?:\+91[\s\-]?|0)?[6-9]\d{4}[\s\-]?\d{5}(?!\d)"),
    "email": re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+"),
    "pan": re.compile(r"\b[A-Z]{3}[PCHFATBLJG][A-Z]\d{4}[A-Z]\b"),
    "aadhaar": re.compile(r"(?<!\d)[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}(?!\d)"),
}


def embedded_matches(text: str) -> set[str]:
    """Which identifier types appear inside a piece of free text."""
    found = set()
    for kind, rx in EMBEDDED.items():
        for m in rx.finditer(text):
            if kind == "aadhaar" and not verhoeff_valid(_digits(m.group())):
                continue
            found.add(kind)
            break
    return found


@dataclass
class ColumnFinding:
    detector: Detector
    confidence: str  # high, medium
    matched: int
    sampled: int
    hint_matched: bool
    example: str = ""
    minors: int = 0
    embedded_types: list[str] = field(default_factory=list)

    @property
    def ratio(self) -> float:
        return self.matched / self.sampled if self.sampled else 0.0


_RANK = {"high": 2, "medium": 1}


def normalize_name(name: str) -> str:
    """'Roll_No', 'roll-no' and 'Roll No' all become 'Roll No' for hint matching."""
    return re.sub(r"[\s_\-./\\,:;()\[\]#|*]+", " ", name).strip()


def classify_column(name: str, values: list[str], today: Optional[date] = None) -> Optional[ColumnFinding]:
    """Decide what kind of personal data a column holds, if any."""
    vals = [v.strip() for v in values if v is not None and str(v).strip() != ""]
    vals = [str(v) for v in vals]
    if not vals:
        return None
    n = len(vals)
    best: Optional[ColumnFinding] = None

    key = normalize_name(name)
    for det in DETECTORS:
        hint = bool(det.hint.search(key))
        if det.id == "person_name" and NOT_PERSON_NAME.search(key):
            hint = False
        if det.needs_hint and not hint:
            continue
        matched = sum(1 for v in vals if det.test(v))
        ratio = matched / n

        if ratio >= 0.8 and (hint or not det.needs_hint):
            conf = "high" if (hint or ratio >= 0.95) else "medium"
        elif hint and ratio >= 0.5:
            conf = "medium"
        elif hint and det.hint_only_ok:
            conf = "medium"
        elif det.id == "caste" and ratio >= 0.8:
            conf = "medium"
        else:
            continue

        cand = ColumnFinding(det, conf, matched, n, hint)
        if best is None or _better(cand, best):
            best = cand

    if best is None:
        return None

    example_src = next((v for v in vals if best.detector.test(v)), vals[0])
    best.example = best.detector.mask(example_src)

    if best.detector.id == "dob":
        ref = today or date.today()
        best.minors = sum(
            1 for v in vals if (d := parse_date(v)) is not None and age_on(d, ref) < 18
        )
    return best


def _better(a: ColumnFinding, b: ColumnFinding) -> bool:
    """Prefer higher confidence, then a matching column name, then match ratio."""
    ka = (_RANK[a.confidence], a.hint_matched, a.ratio)
    kb = (_RANK[b.confidence], b.hint_matched, b.ratio)
    return ka > kb


def scan_free_text(values: list[str]) -> tuple[list[str], int]:
    """Look for identifiers hidden inside free text. Returns (types, rows_hit)."""
    types: set[str] = set()
    rows = 0
    for v in values:
        if not v or len(str(v)) < 8:
            continue
        hit = embedded_matches(str(v))
        if hit:
            rows += 1
            types |= hit
    return sorted(types), rows
