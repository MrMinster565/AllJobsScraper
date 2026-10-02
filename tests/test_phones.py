import pytest

from alljobs.phones import extract_phones


@pytest.mark.parametrize(
    "text,expected",
    [
        ("לפרטים: 050-1234567", ["050-1234567"]),
        ("התקשרו 0501234567 או 052 123 4567", ["050-1234567", "052-1234567"]),
        ("משרד: 03-5551234", ["03-5551234"]),
        ("tel +972-54-9876543", ["054-9876543"]),
        ("tel 972 (0) 3 555 1234", ["03-5551234"]),
        ("00972501234567", ["050-1234567"]),
        ("1-700-505-050", ["1-700-505-050"]),
        ("072-2345678", ["072-2345678"]),
    ],
)
def test_extracts(text, expected):
    assert extract_phones(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "תאריך 02/03/2024",
        "מספר משרה 123456789012",
        "שכר 12,000-15,000 ש\"ח",
        "05012345678901",  # too many digits: not a phone
        "",
    ],
)
def test_ignores_non_phones(text):
    assert extract_phones(text) == []


def test_dedupes():
    assert extract_phones("050-1234567, 0501234567, +972501234567") == ["050-1234567"]
