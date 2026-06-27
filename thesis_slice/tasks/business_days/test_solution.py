from solution import add_business_days


def test_forward_over_weekend():
    # 2026-06-26 is a Friday; +1 business day -> Monday
    assert add_business_days("2026-06-26", 1, []) == "2026-06-29"


def test_forward_skips_holiday():
    assert add_business_days("2026-06-26", 1, ["2026-06-29"]) == "2026-06-30"


def test_forward_full_week():
    assert add_business_days("2026-06-22", 5, []) == "2026-06-29"


def test_backward():
    assert add_business_days("2026-06-29", -1, []) == "2026-06-26"


def test_zero_returns_start_unchanged():
    # Saturday, returned as-is
    assert add_business_days("2026-06-27", 0, []) == "2026-06-27"
