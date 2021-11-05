import pytest

from sqlfmt.mode import Mode


@pytest.mark.parametrize(
    "no_color,force_color,env_no_color,result",
    [
        (True, False, False, False),
        (False, False, True, False),
        (True, False, True, False),
        (True, True, True, True),
        (True, True, False, True),
        (False, True, True, True),
        (False, False, False, True),
    ],
)
def test_color_mode(
    no_color: bool,
    force_color: bool,
    env_no_color: bool,
    result: bool,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    if env_no_color:
        monkeypatch.setenv("NO_COLOR", "1")
    else:
        monkeypatch.delenv("NO_COLOR", raising=False)

    mode = Mode(_no_color=no_color, _force_color=force_color)

    assert mode.color is result
