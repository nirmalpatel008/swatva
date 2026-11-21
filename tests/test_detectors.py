from datetime import date

from swatva.detectors import (
    classify_column,
    embedded_matches,
    is_aadhaar,
    is_ifsc,
    is_pan,
    is_phone,
    mask_email,
    mask_keep_last4,
    mask_name,
    verhoeff_check_digit,
    verhoeff_valid,
)


def make_aadhaar(body: str) -> str:
    return body + verhoeff_check_digit(body)


def test_verhoeff_round_trip():
    for body in ["23456789012", "98765432101", "50000000000"]:
        assert verhoeff_valid(make_aadhaar(body))


def test_verhoeff_catches_single_digit_error():
    good = make_aadhaar("23456789012")
    bad = good[:-1] + str((int(good[-1]) + 1) % 10)
    assert not verhoeff_valid(bad)


def test_aadhaar_accepts_spaces_and_rejects_bad_first_digit():
    a = make_aadhaar("34567890123")
    assert is_aadhaar(a)
    assert is_aadhaar(f"{a[:4]} {a[4:8]} {a[8:]}")
    assert not is_aadhaar(make_aadhaar("14567890123"))  # Aadhaar never starts with 0 or 1


def test_pan_ifsc_phone():
    assert is_pan("ABCPE1234F")
    assert not is_pan("ABCXE1234F")  # 4th character must be a valid holder type
    assert is_ifsc("SBIN0001234")
    assert not is_ifsc("SBIN1001234")  # 5th character is always 0
    assert is_phone("9876543210")
    assert is_phone("+91 98765 43210")
    assert not is_phone("5876543210")


def test_masks_never_show_full_value():
    assert mask_keep_last4("9876543210") == "XXXXXX3210"
    assert mask_email("ravi.patel@gmail.com") == "r***@gmail.com"
    assert mask_name("Ravi Kumar Patel") == "R. K. P."


def test_bank_account_needs_column_hint():
    nums = ["123456789012", "998877665544332", "11122233344"] * 5
    assert classify_column("ref_number", nums) is None
    f = classify_column("bank_account_no", nums)
    assert f and f.detector.id == "bank_account"


def test_apaar_vs_aadhaar_by_column_name():
    ids = ["482910374615", "119283746501", "730192837465"] * 5
    f = classify_column("apaar_id", ids)
    assert f and f.detector.id == "apaar"


def test_aadhaar_found_without_hint_when_checksums_pass():
    vals = [make_aadhaar(str(30000000000 + i * 7919)) for i in range(20)]
    f = classify_column("uid_field_7", vals)
    assert f and f.detector.id == "aadhaar"


def test_not_a_person_name():
    subjects = ["Cloud Computing", "Software Engineering", "Artificial Intelligence"] * 5
    assert classify_column("Subject Name", subjects) is None
    assert classify_column("hostel_name", ["Boys Hostel A", "Girls Hostel"] * 5) is None


def test_gujarati_names_detected():
    f = classify_column("student_name_gujarati", ["આરવ પટેલ", "દિયા શાહ", "ઈશા દેસાઈ"] * 4)
    assert f and f.detector.id == "person_name"


def test_minors_counted_from_dob():
    today = date(2026, 11, 20)
    vals = ["01-01-2010", "15-06-2000", "30-11-2008", "21-11-2008"]
    f = classify_column("dob", vals, today=today)
    assert f and f.detector.id == "dob"
    assert f.minors == 3  # the one born 21-11-2008 turns 18 tomorrow


def test_caste_detected_from_values_alone():
    f = classify_column("col_9", ["OBC", "GEN", "SC", "ST", "SEBC", "EWS"] * 3)
    assert f and f.detector.id == "caste"


def test_identifiers_hidden_in_free_text():
    assert embedded_matches("call father on 98250 12345 if late") == {"phone"}
    assert "email" in embedded_matches("guardian email x.y@gmail.com")
    assert embedded_matches("Room changed on request") == set()
