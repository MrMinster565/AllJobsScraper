"""Find Israeli phone numbers in free text (Hebrew or English job ads)."""
from __future__ import annotations

import re

_SEP = r"[ \t.\-]?"

# National format: 05X (mobile), 07X (VoIP / company lines), 02/03/04/08/09 (landline).
_NATIONAL = rf"0(?:5\d|7\d|[2-489]){_SEP}\d{{3}}{_SEP}\d{{4}}"
# International: +972-5X-..., 972 50 ..., 00972..., optionally with the "(0)" some ads keep.
_INTL = rf"(?:\+|00)?972{_SEP}(?:\(0\))?{_SEP}0?(?:5\d|7\d|[2-489]){_SEP}\d{{3}}{_SEP}\d{{4}}"
# Toll-free / shared-cost: 1-700-XXX-XXX, 1-800-XXX-XXX, 1-599-XXX-XXX.
_SPECIAL = rf"1{_SEP}(?:700|800|599){_SEP}\d{{3}}{_SEP}\d{{3}}"

_PHONE_RE = re.compile(rf"(?<![\d+])(?:{_INTL}|{_NATIONAL}|{_SPECIAL})(?!\d)")


def _normalize(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("00972"):
        digits = digits[5:]
    elif digits.startswith("972"):
        digits = digits[3:]
    if digits[:1] in "123456789" and not digits.startswith("1"):
        digits = "0" + digits
    if digits.startswith("1"):  # 1-700 / 1-800 / 1-599
        return f"{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"
    if digits.startswith(("05", "07")):  # 10 digits: 05X-XXXXXXX
        return f"{digits[:3]}-{digits[3:]}"
    return f"{digits[:2]}-{digits[2:]}"  # 9 digits: 0X-XXXXXXX


def extract_phones(text: str) -> list[str]:
    """Return unique phone numbers found in `text`, normalized (e.g. 050-1234567), in order."""
    found: list[str] = []
    for m in _PHONE_RE.finditer(text or ""):
        number = _normalize(m.group(0))
        if number not in found:
            found.append(number)
    return found
