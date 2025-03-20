"""
Utilities for memory management and object size calculation.
"""

from __future__ import annotations

import sys
from collections import deque
from collections.abc import Callable
from itertools import chain
from typing import Any


def total_size(
    o: Any, handlers: dict[type, Callable] | None = None, verbose: bool = False
) -> int:
    """
    Returns the approximate memory footprint of an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses: tuple, list, deque, dict, set and frozenset.

    To search other containers, add handlers to iterate over their contents:
        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    Args:
        o: The object to measure
        handlers: Optional dictionary of custom handlers for container types
        verbose: If True, prints details about each object measured

    Returns:
        Total size in bytes
    """
    if handlers is None:
        handlers = {}

    def dict_handler(d):
        return chain.from_iterable(d.items())

    all_handlers = {
        tuple: iter,
        list: iter,
        deque: iter,
        dict: dict_handler,
        set: iter,
        frozenset: iter,
    }
    all_handlers.update(handlers)  # user handlers take precedence
    seen: set[int] = set()  # track which object id's have already been seen
    default_size = sys.getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(obj: Any) -> int:
        """Recursively calculate size of object and its contents."""
        if id(obj) in seen:  # do not double count the same object
            return 0
        seen.add(id(obj))
        size = sys.getsizeof(obj, default_size)

        if verbose:
            print(size, type(obj), repr(obj)[:100])  # limit repr to avoid huge output

        for typ, handler in all_handlers.items():
            if isinstance(obj, typ):
                size += sum(map(sizeof, handler(obj)))
                break
        return size

    return sizeof(o)
