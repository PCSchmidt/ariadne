from solution import top_n_words


def test_basic_counts():
    assert top_n_words("the cat the dog the", 2) == [("the", 3), ("cat", 1)]


def test_tie_broken_alphabetically():
    assert top_n_words("a a b b c", 2) == [("a", 2), ("b", 2)]


def test_case_insensitive_and_punctuation():
    assert top_n_words("The, the! THE.", 1) == [("the", 3)]


def test_empty():
    assert top_n_words("", 3) == []
