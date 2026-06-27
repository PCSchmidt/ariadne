from solution import evaluate


def test_precedence():
    assert evaluate("2+3*4") == 14.0


def test_parentheses():
    assert evaluate("(2+3)*4") == 20.0


def test_unary_minus():
    assert evaluate("-3+4*2") == 5.0
    assert evaluate("(1+2)*-3") == -9.0


def test_float_division():
    assert evaluate("10/4") == 2.5


def test_left_associative():
    assert evaluate("10-2-3") == 5.0
    assert evaluate("100/10/2") == 5.0
