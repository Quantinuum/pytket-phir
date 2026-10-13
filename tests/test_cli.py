##############################################################################
#
# Copyright (c) 2026 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

from ast import literal_eval
from importlib.metadata import version
from typing import TYPE_CHECKING

import pytest

from pytket.phir.cli import main

from .test_utils import WatFile, get_wat_as_wasm_bytes

if TYPE_CHECKING:
    from pathlib import Path


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


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            "qreg q[1]; creg c[1]; x q[0]; measure q[0] -> c[0];",
            {"c": ["1"] * 10},
        ),
        (
            "creg a[3]; creg b[3]; a = 7; b = a;",
            {"a": ["111"] * 10, "b": ["111"] * 10},
        ),
        (
            (
                "qreg q[2]; creg c[3]; x q[0]; measure q[0] -> c[2]; "
                "if (c == 4) x q[1]; measure q[1] -> c[0];"
            ),
            {"c": ["101"] * 10},
        ),
    ],
)
def test_cli_emulation(
    tmp_path: "Path",
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    body: str,
    expected: dict[str, list[str]],
) -> None:
    """Emulate QASM, including high register bits and measurement feed-forward."""
    qasm_file = tmp_path / "program.qasm"
    qasm_file.write_text(
        f'OPENQASM 2.0; include "qelib1.inc"; {body}', encoding="utf-8"
    )
    monkeypatch.setattr("sys.argv", ["phirc", str(qasm_file)])

    main()

    output = capsys.readouterr().out.split("PECOS results:\n")[1]
    assert literal_eval(output) == expected


def test_cli_wasm_emulation(
    tmp_path: "Path",
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Emulate a WASM call after measurement and multiple-bit register copying."""
    qasm_file = tmp_path / "program.qasm"
    qasm_file.write_text(
        'OPENQASM 2.0; include "qelib1.inc"; '
        "qreg q[1]; creg a[3]; creg b[3]; creg result[3]; "
        "x q[0]; measure q[0] -> a[0]; b = a; result = add(a, b);",
        encoding="utf-8",
    )
    wasm_file = tmp_path / "add.wasm"
    wasm_file.write_bytes(get_wat_as_wasm_bytes(WatFile.add))
    monkeypatch.setattr(
        "sys.argv", ["phirc", str(qasm_file), "--wasm-file", str(wasm_file)]
    )

    main()

    output = capsys.readouterr().out.split("PECOS results:\n")[1]
    assert literal_eval(output) == {
        "a": ["001"] * 10,
        "b": ["001"] * 10,
        "result": ["010"] * 10,
    }
