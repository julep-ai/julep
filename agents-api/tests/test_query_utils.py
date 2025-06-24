from agents_api.queries.utils import sanitize_string


def test_utility_sanitize_string_strings():
    """utility: sanitize_string - strings"""
    assert sanitize_string("test\x00string") == "teststring"
    assert sanitize_string("normal string") == "normal string"
    assert sanitize_string("multiple\x00null\x00chars") == "multiplenullchars"
    assert sanitize_string("") == ""
    assert sanitize_string(None) is None


def test_utility_sanitize_string_nested_data_structures():
    """utility: sanitize_string - nested data structures"""
    test_dict = {
        "key1": "value\x00",
        "key2": ["item\x001", "item2"],
        "key3": {"nested_key": "nested\x00value"},
    }
    expected_dict = {
        "key1": "value",
        "key2": ["item1", "item2"],
        "key3": {"nested_key": "nestedvalue"},
    }
    assert sanitize_string(test_dict) == expected_dict
    test_list = ["item\x001", {"key": "value\x00"}, ["nested\x00item"]]
    expected_list = ["item1", {"key": "value"}, ["nesteditem"]]
    assert sanitize_string(test_list) == expected_list
    test_tuple = ("item\x001", "item2")
    expected_tuple = ("item1", "item2")
    assert sanitize_string(test_tuple) == expected_tuple


def test_utility_sanitize_string_non_string_types():
    """utility: sanitize_string - non-string types"""
    assert sanitize_string(123) == 123
    assert sanitize_string(123.45) == 123.45
    assert sanitize_string(True) is True
    assert sanitize_string(False) is False
