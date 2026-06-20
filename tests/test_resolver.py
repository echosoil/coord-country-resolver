from country_resolver import coord_to_float


def test_coord_to_float_accepts_decimal_comma():
    assert coord_to_float("35,25") == 35.25


def test_coord_to_float_accepts_decimal_dot():
    assert coord_to_float("35.25") == 35.25


def test_coord_to_float_rejects_bad_values():
    assert coord_to_float(None) is None
    assert coord_to_float("") is None
    assert coord_to_float("bad") is None