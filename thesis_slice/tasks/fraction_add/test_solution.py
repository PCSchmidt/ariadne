from solution import add


def test_simple():
    assert add((1, 2), (1, 3)) == (5, 6)


def test_reduces_to_whole():
    assert add((1, 2), (1, 2)) == (1, 1)


def test_reduces_to_lowest_terms():
    assert add((2, 4), (1, 4)) == (3, 4)


def test_zero_canonical():
    assert add((1, 2), (-1, 2)) == (0, 1)


def test_negative_denominator_normalized():
    assert add((1, -2), (1, 2)) == (0, 1)
    assert add((-1, 3), (-1, 6)) == (-1, 2)
