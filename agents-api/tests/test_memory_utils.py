"""
Tests for the memory utilities module.
"""

import sys
from collections import deque

from agents_api.common.utils.memory import total_size


def test_total_size_basic_types():
    """total_size calculates correct size for basic types"""
    assert total_size(42) == sys.getsizeof(42)
    assert total_size(3.14) == sys.getsizeof(3.14)
    assert total_size("hello") == sys.getsizeof("hello")
    assert total_size(True) == sys.getsizeof(True)
    assert total_size(None) == sys.getsizeof(None)


def test_total_size_containers():
    """total_size correctly handles container types"""
    lst = [1, 2, 3, 4, 5]
    expected_min = sys.getsizeof(lst) + sum(sys.getsizeof(i) for i in lst)
    assert total_size(lst) == expected_min
    tup = (1, 2, 3, 4, 5)
    expected_min = sys.getsizeof(tup) + sum(sys.getsizeof(i) for i in tup)
    assert total_size(tup) == expected_min
    d = {"a": 1, "b": 2, "c": 3}
    expected_min = sys.getsizeof(d) + sum(
        (sys.getsizeof(k) + sys.getsizeof(v) for k, v in d.items())
    )
    assert total_size(d) == expected_min
    s = {1, 2, 3, 4, 5}
    expected_min = sys.getsizeof(s) + sum(sys.getsizeof(i) for i in s)
    assert total_size(s) == expected_min
    dq = deque([1, 2, 3, 4, 5])
    expected_min = sys.getsizeof(dq) + sum(sys.getsizeof(i) for i in dq)
    assert total_size(dq) == expected_min


def test_total_size_nested():
    """total_size correctly handles nested objects"""
    nested_list = [1, [2, 3], [4, [5, 6]]]
    assert total_size(nested_list) > sys.getsizeof(nested_list)
    nested_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
    assert total_size(nested_dict) > sys.getsizeof(nested_dict)
    complex_obj: dict[str, list[tuple[int, set[int]]]] = {
        "data": [(1, {2, 3}), (4, {5, 6})],
        "meta": [(7, {8, 9}), (10, {11, 12})],
    }
    assert total_size(complex_obj) > sys.getsizeof(complex_obj)


def test_total_size_custom_objects():
    """total_size handles custom objects"""

    class Person:
        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    person = Person("John", 30)
    empty_person = Person("", 0)
    assert total_size(person) > 0
    assert total_size(person) == total_size(empty_person)

    def person_handler(p):
        return p.__dict__.values()

    assert total_size(person, handlers={Person: person_handler}) > total_size(
        empty_person, handlers={Person: person_handler}
    )


def test_total_size_circular_refs():
    """total_size handles objects with circular references"""
    a = [1, 2, 3]
    a.append(a)
    size = total_size(a)
    assert size > 0
    b: dict = {"key": 1}
    b["self"] = b
    size = total_size(b)
    assert size > 0


def test_total_size_custom_handlers():
    """total_size with custom handlers"""

    class CustomContainer:
        def __init__(self, items):
            self.items = items

        def get_items(self):
            return self.items

    container = CustomContainer([1, 2, 3, 4, 5])
    size_without_handler = total_size(container)
    handlers = {CustomContainer: lambda c: c.get_items()}
    size_with_handler = total_size(container, handlers=handlers)
    assert size_with_handler >= size_without_handler
