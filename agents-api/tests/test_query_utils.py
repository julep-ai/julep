from agents_api.queries.utils import sanitize_pg_string
from ward import test


@test("utility: sanitize_pg_string - strings")
def _():
    # Test basic string sanitization
    assert sanitize_pg_string("test\u0000string") == "teststring"
    assert sanitize_pg_string("normal string") == "normal string"
    assert sanitize_pg_string("multiple\u0000null\u0000chars") == "multiplenullchars"
    assert sanitize_pg_string("") == ""
    assert sanitize_pg_string(None) is None


@test("utility: sanitize_pg_string - nested data structures")
def _():
    # Test dictionary sanitization
    test_dict = {
        "key1": "value\u0000",
        "key2": ["item\u00001", "item2"],
        "key3": {"nested_key": "nested\u0000value"}
    }
    expected_dict = {
        "key1": "value",
        "key2": ["item1", "item2"],
        "key3": {"nested_key": "nestedvalue"}
    }
    assert sanitize_pg_string(test_dict) == expected_dict

    # Test list sanitization
    test_list = ["item\u00001", {"key": "value\u0000"}, ["nested\u0000item"]]
    expected_list = ["item1", {"key": "value"}, ["nesteditem"]]
    assert sanitize_pg_string(test_list) == expected_list

    # Test tuple sanitization
    test_tuple = ("item\u00001", "item2")
    expected_tuple = ("item1", "item2")
    assert sanitize_pg_string(test_tuple) == expected_tuple


@test("utility: sanitize_pg_string - non-string types")
def _():
    # Test non-string types
    assert sanitize_pg_string(123) == 123
    assert sanitize_pg_string(123.45) == 123.45
    assert sanitize_pg_string(True) is True
    assert sanitize_pg_string(False) is False
