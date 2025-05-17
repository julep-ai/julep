from agents_api.queries.utils import sanitize_string
import pytest


def test_utility_sanitize_string_strings():
    """utility: sanitize_string - strings"""
    # Test basic string sanitization
    assert sanitize_string("test\u0000string") == "teststring"
    assert sanitize_string("normal string") == "normal string"
    assert sanitize_string("multiple\u0000null\u0000chars") == "multiplenullchars"
    assert sanitize_string("") == ""
    assert sanitize_string(None) is None


def test_utility_sanitize_string_nested_data_structures():
    """utility: sanitize_string - nested data structures"""
    # Test dictionary sanitization
    test_dict = {
        "key1": "value\u0000",
        "key2": ["item\u00001", "item2"],
        "key3": {"nested_key": "nested\u0000value"},
    }
    expected_dict = {
        "key1": "value",
        "key2": ["item1", "item2"],
        "key3": {"nested_key": "nestedvalue"},
    }
    assert sanitize_string(test_dict) == expected_dict

    # Test list sanitization
    test_list = ["item\u00001", {"key": "value\u0000"}, ["nested\u0000item"]]
    expected_list = ["item1", {"key": "value"}, ["nesteditem"]]
    assert sanitize_string(test_list) == expected_list

    # Test tuple sanitization
    test_tuple = ("item\u00001", "item2")
    expected_tuple = ("item1", "item2")
    assert sanitize_string(test_tuple) == expected_tuple


def test_utility_sanitize_string_non_string_types():
    """utility: sanitize_string - non-string types"""
    # Test non-string types
    assert sanitize_string(123) == 123
    assert sanitize_string(123.45) == 123.45
    assert sanitize_string(True) is True
    assert sanitize_string(False) is False
