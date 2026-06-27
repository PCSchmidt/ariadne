from solution import compare


def test_numeric_core():
    assert compare("1.0.0", "1.0.1") == -1
    assert compare("2.0.0", "1.9.9") == 1
    assert compare("1.2.0", "1.2.0") == 0


def test_prerelease_lower_than_release():
    assert compare("1.0.0-alpha", "1.0.0") == -1
    assert compare("1.0.0", "1.0.0-alpha") == 1


def test_prerelease_field_count():
    assert compare("1.0.0-alpha", "1.0.0-alpha.1") == -1


def test_numeric_vs_alpha_identifier():
    assert compare("1.0.0-alpha.1", "1.0.0-alpha.beta") == -1


def test_build_metadata_ignored():
    assert compare("1.0.0+build.99", "1.0.0") == 0
