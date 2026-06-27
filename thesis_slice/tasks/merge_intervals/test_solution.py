from solution import merge


def test_overlapping():
    assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]


def test_touching_endpoints():
    assert merge([[1, 4], [4, 5]]) == [[1, 5]]


def test_unsorted_input():
    assert merge([[8, 10], [1, 3], [2, 6]]) == [[1, 6], [8, 10]]


def test_empty():
    assert merge([]) == []
