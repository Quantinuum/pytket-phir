##############################################################################
#
# Copyright (c) 2023 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import logging

import pytest
from pytket.circuit import Bit, Circuit, Qubit

from pytket.phir.api import IncompleteRegisterError, pytket_to_phir, qasm_to_phir
from pytket.phir.qtm_machine import QtmMachine

from .test_utils import QasmFile, get_qasm_as_circuit

logger = logging.getLogger(__name__)


class TestApi:
    def test_pytket_to_phir_no_machine(self) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(QasmFile.baby)
        assert pytket_to_phir(circuit)

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_no_machine_all(self, test_file: QasmFile) -> None:
        """Test case when no machine is present."""
        circuit = get_qasm_as_circuit(test_file)

        match test_file:
            case QasmFile.big_gate:
                with pytest.raises(KeyError, match=r".*CnX.*"):
                    assert pytket_to_phir(circuit)
            case QasmFile.qv20_0:
                with pytest.raises(KeyError, match=r".*U3.*"):
                    assert pytket_to_phir(circuit)
            case _:
                assert pytket_to_phir(circuit)

    @pytest.mark.parametrize("test_file", list(QasmFile))
    def test_pytket_to_phir_h1_1_all(self, test_file: QasmFile) -> None:
        """Standard case."""
        circuit = get_qasm_as_circuit(test_file)

        assert pytket_to_phir(circuit, QtmMachine.H1)

    def test_qasm_to_phir(self) -> None:
        """Test the qasm string entrypoint works."""
        qasm = """
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[3];
        h q;
        ZZ q[1],q[0];
        creg cr[3];
        measure q[0]->cr[0];
        measure q[1]->cr[0];
        """

        assert qasm_to_phir(qasm, QtmMachine.H1)

    def test_incomplete_qubit_register(self) -> None:
        """Test that incomplete qubit registers are rejected.

        From https://github.com/Quantinuum/pytket-phir/issues/242
        """
        circ = Circuit()
        circ.add_qubit(Qubit(1))
        circ.add_bit(Bit(1))
        circ.H(1)
        circ.Measure(1, 1)

        with pytest.raises(
            IncompleteRegisterError,
            match=r".*incomplete qubit registers.*incomplete bit registers.*",
        ):
            pytket_to_phir(circ)

    def test_incomplete_qubit_register_1(self) -> None:
        """Test that incomplete qubit registers are rejected."""
        circ = Circuit()
        circ.add_qubit(Qubit(1))

        with pytest.raises(
            IncompleteRegisterError,
            match=r".*incomplete qubit registers.*",
        ):
            pytket_to_phir(circ)

    def test_incomplete_bit_register_1(self) -> None:
        """Test that incomplete bit registers are rejected."""
        circ = Circuit()
        circ.add_bit(Bit(1))

        with pytest.raises(
            IncompleteRegisterError,
            match=r".*incomplete bit registers.*",
        ):
            pytket_to_phir(circ)

    def test_incomplete_qubit_register_with_gap(self) -> None:
        """Test that qubit registers with gaps are rejected."""
        circ = Circuit()
        circ.add_qubit(Qubit(0))
        circ.add_qubit(Qubit(2))
        circ.H(0)
        circ.H(2)

        with pytest.raises(
            IncompleteRegisterError, match=r".*incomplete qubit registers.*"
        ):
            pytket_to_phir(circ)

    def test_incomplete_bit_register(self) -> None:
        """Test that incomplete bit registers are rejected."""
        circ = Circuit()
        circ.add_q_register("q", 2)
        circ.add_bit(Bit(1))
        circ.H(0)
        circ.Measure(0, 1)

        with pytest.raises(
            IncompleteRegisterError, match=r".*incomplete bit registers.*"
        ):
            pytket_to_phir(circ)
