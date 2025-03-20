"""
Tests for the memory utilities module.
"""

import sys
from collections import deque

from agents_api.common.utils.memory import total_size
from ward import test


@test("total_size calculates correct size for basic types")
def test_total_size_basic_types():
    # Integer
    assert total_size(42) == sys.getsizeof(42)

    # Float
    assert total_size(3.14) == sys.getsizeof(3.14)

    # String
    assert total_size("hello") == sys.getsizeof("hello")

    # Boolean
    assert total_size(True) == sys.getsizeof(True)

    # None
    assert total_size(None) == sys.getsizeof(None)


@test("total_size correctly handles container types")
def test_total_size_containers():
    # List
    lst = [1, 2, 3, 4, 5]
    expected_min = sys.getsizeof(lst) + sum(sys.getsizeof(i) for i in lst)
    assert total_size(lst) == expected_min

    # Tuple
    tup = (1, 2, 3, 4, 5)
    expected_min = sys.getsizeof(tup) + sum(sys.getsizeof(i) for i in tup)
    assert total_size(tup) == expected_min

    # Dictionary
    d = {"a": 1, "b": 2, "c": 3}
    expected_min = sys.getsizeof(d) + sum(
        sys.getsizeof(k) + sys.getsizeof(v) for k, v in d.items()
    )
    assert total_size(d) == expected_min

    # Set
    s = {1, 2, 3, 4, 5}
    expected_min = sys.getsizeof(s) + sum(sys.getsizeof(i) for i in s)
    assert total_size(s) == expected_min

    # Deque
    dq = deque([1, 2, 3, 4, 5])
    expected_min = sys.getsizeof(dq) + sum(sys.getsizeof(i) for i in dq)
    assert total_size(dq) == expected_min


@test("total_size correctly handles nested objects")
def test_total_size_nested():
    # Simple nested list
    nested_list = [1, [2, 3], [4, [5, 6]]]
    assert total_size(nested_list) > sys.getsizeof(nested_list)

    # Simple nested dict
    nested_dict = {"a": 1, "b": {"c": 2, "d": {"e": 3}}}
    assert total_size(nested_dict) > sys.getsizeof(nested_dict)

    # Complex structure with type hints
    complex_obj: dict[str, list[tuple[int, set[int]]]] = {
        "data": [(1, {2, 3}), (4, {5, 6})],
        "meta": [(7, {8, 9}), (10, {11, 12})],
    }
    assert total_size(complex_obj) > sys.getsizeof(complex_obj)


@test("total_size handles custom objects")
def test_total_size_custom_objects():
    class Person:
        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

    person = Person("John", 30)
    empty_person = Person("", 0)  # This will have smaller attribute values

    # The person with longer strings should take more space
    assert total_size(person) > 0

    # NOTE: total_size does not recurse into __dict__ for custom objects by default
    # This is expected behavior since it only has built-in handlers for standard containers
    # The size is equal because it only measures the object's basic size, not its attributes
    assert total_size(person) == total_size(empty_person)

    # Let's add a test with a custom handler that does inspect the object's __dict__
    def person_handler(p):
        return p.__dict__.values()

    # With a custom handler, we should see different sizes
    assert total_size(person, handlers={Person: person_handler}) > total_size(
        empty_person, handlers={Person: person_handler}
    )


@test("total_size handles objects with circular references")
def test_total_size_circular_refs():
    # List with circular reference
    a = [1, 2, 3]
    a.append(a)  # a contains itself

    # This should not cause an infinite recursion
    size = total_size(a)
    assert size > 0

    # Dictionary with circular reference
    b: dict = {"key": 1}
    b["self"] = b  # b contains itself

    # This should not cause an infinite recursion
    size = total_size(b)
    assert size > 0


@test("total_size with custom handlers")
def test_total_size_custom_handlers():
    class CustomContainer:
        def __init__(self, items):
            self.items = items

        def get_items(self):
            return self.items

    container = CustomContainer([1, 2, 3, 4, 5])

    # Without a custom handler
    size_without_handler = total_size(container)

    # With a custom handler
    handlers = {CustomContainer: lambda c: c.get_items()}
    size_with_handler = total_size(container, handlers=handlers)

    # The handler accounts for the contained items
    assert size_with_handler >= size_without_handler
