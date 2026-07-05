# tests/test_fragments.py
from julep.prompt import Lift, Ask, Concat, Under, Map, fragments


def test_lift_is_constant() -> None:
    assert Lift("x").render({"any": 1}) == "x"


def test_ask_reads_field_with_formatter() -> None:
    assert Ask("who", fmt=lambda v: f"[{v}]").render({"who": "ada"}) == "[ada]"
    assert Ask("missing").render({}) == ""           # default "" then str("") == ""


def test_concat_is_string_monoid() -> None:
    f = fragments("a", Ask("b"), "c")                # str auto-lifts
    assert f.render({"b": "B"}) == "aBc"
    assert Concat(()).render({}) == ""               # identity


def test_under_contramaps_the_environment() -> None:
    inner = Ask("name")
    f = Under(lambda c: c["user"], inner)
    assert f.render({"user": {"name": "ada"}}) == "ada"


def test_map_post_processes_output() -> None:
    assert Map(Lift("hi"), str.upper).render({}) == "HI"
