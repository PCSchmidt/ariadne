from solution import justify


def test_basic_even_distribution():
    assert justify(["This", "is", "an", "example", "of", "text", "justification."], 16) == [
        "This    is    an",
        "example  of text",
        "justification.  ",
    ]


def test_left_heavy_uneven_spaces():
    assert justify(["What", "must", "be", "acknowledgment", "shall", "be"], 16) == [
        "What   must   be",
        "acknowledgment  ",
        "shall be        ",
    ]


def test_single_word_line_padded():
    assert justify(["hello"], 10) == ["hello     "]


def test_last_line_left_justified():
    out = justify(["a", "b", "c", "d"], 5)
    assert all(len(line) == 5 for line in out)
    assert out[-1] == out[-1].rstrip().ljust(5)
