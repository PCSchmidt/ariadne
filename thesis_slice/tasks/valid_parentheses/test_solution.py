from solution import is_valid


def test_simple_pairs():
    assert is_valid("()") is True
    assert is_valid("()[]{}") is True


def test_nested():
    assert is_valid("{[]}") is True


def test_mismatch():
    assert is_valid("(]") is False
    assert is_valid("([)]") is False


def test_empty():
    assert is_valid("") is True
