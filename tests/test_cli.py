##############################################################################
#
# Copyright (c) 2026 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from importlib.metadata import version

import pytest

from pytket.phir.cli import main


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("--help", "Emulates QASM program execution via PECOS"),
        ("--version", version("pytket-phir")),
    ],
)
def test_cli_information_without_emulation_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    option: str,
    expected: str,
) -> None:
    """CLI information works with only the core package installed."""
    monkeypatch.setattr("sys.argv", ["phirc", option])
    with pytest.raises(SystemExit, match=r"^0$"):
        main()
    assert expected in capsys.readouterr().out
