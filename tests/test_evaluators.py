from types import SimpleNamespace

from agent_eval_matrix.evaluators import FileContentMatch, _normalize


def test_normalize() -> None:
    assert _normalize("a\r\nb") == "a\nb"


def test_file_content_match_pass() -> None:
    ev = FileContentMatch()
    ctx = SimpleNamespace(output="hello", expected_output="hello")
    assert ev.evaluate(ctx) == 1.0


def test_file_content_match_fail() -> None:
    ev = FileContentMatch()
    ctx = SimpleNamespace(output="hello", expected_output="world")
    assert ev.evaluate(ctx) == 0.0
