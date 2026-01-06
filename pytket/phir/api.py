##############################################################################
#
# Copyright (c) 2023-2024 Quantinuum LLC All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.
#
##############################################################################

# mypy: disable-error-code="misc"

import logging
from collections import defaultdict
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from pytket.qasm.qasm import circuit_from_qasm_str, circuit_from_qasm_wasm
from rich import print  # noqa: A004

from phir.model import PHIRModel

from .phirgen import WORDSIZE, genphir
from .phirgen_parallel import genphir_parallel
from .place_and_route import place_and_route
from .qtm_machine import QTM_MACHINES_MAP, QtmMachine
from .rebasing.rebaser import rebase_to_qtm_machine
from .sharding.sharder import Sharder

if TYPE_CHECKING:
    from pytket.circuit import Circuit

    from .machine import Machine

logger = logging.getLogger(__name__)


class IncompleteRegisterError(Exception):
    """Exception raised when a circuit contains incomplete registers."""

    def __init__(
        self, incomplete_qubits: list[str], incomplete_bits: list[str]
    ) -> None:
        """Initialize the exception with details about incomplete registers."""
        msg_parts = []
        if incomplete_qubits:
            msg_parts.append(f"incomplete qubit registers: {incomplete_qubits}")
        if incomplete_bits:
            msg_parts.append(f"incomplete bit registers: {incomplete_bits}")
        msg = (
            "Circuit contains "
            + " and ".join(msg_parts)
            + ". All qubits and bits must form complete registers "
            + "starting from index 0."
        )
        super().__init__(msg)


def _validate_circuit_registers(circuit: "Circuit") -> None:
    """Validate that all qubits and bits form complete registers.

    Raises:
        IncompleteRegisterError: If the circuit contains incomplete registers
    """
    # Group qubits by register name
    qubit_registers: dict[str, set[int]] = defaultdict(set)
    for qubit in circuit.qubits:  # noqa: FURB142, RUF100
        qubit_registers[qubit.reg_name].add(qubit.index[0])

    # Group bits by register name
    bit_registers: dict[str, set[int]] = defaultdict(set)
    for bit in circuit.bits:  # noqa: FURB142, RUF100
        bit_registers[bit.reg_name].add(bit.index[0])

    # Check for incomplete qubit registers
    incomplete_qubits = []
    for reg_name, indices in qubit_registers.items():
        expected_indices = set(range(len(indices)))
        if indices != expected_indices:
            incomplete_qubits.append(f"{reg_name}{sorted(indices)}")

    # Check for incomplete bit registers
    incomplete_bits = []
    for reg_name, indices in bit_registers.items():
        expected_indices = set(range(len(indices)))
        if indices != expected_indices:
            incomplete_bits.append(f"{reg_name}{sorted(indices)}")

    if incomplete_qubits or incomplete_bits:
        raise IncompleteRegisterError(incomplete_qubits, incomplete_bits)


def pytket_to_phir(circuit: "Circuit", qtm_machine: QtmMachine | None = None) -> str:
    """Converts a pytket circuit into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param circuit: Circuit object to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against

    Returns:
        PHIR JSON as a str

    Raises:
        IncompleteRegisterError: If the circuit contains incomplete registers
    """
    logger.info("Starting phir conversion process for circuit %s", circuit)

    # Validate that all qubits and bits form complete registers
    _validate_circuit_registers(circuit)

    machine: Machine | None = None
    if qtm_machine:
        logger.info("Rebasing to machine %s", qtm_machine)
        circuit = rebase_to_qtm_machine(circuit, qtm_machine)
        machine = QTM_MACHINES_MAP.get(qtm_machine)
    else:
        machine = None

    logger.debug("Sharding input circuit...")
    shards = Sharder(circuit).shard()

    if machine:
        # Only print message if a machine object is passed
        # Otherwise, placement and routing are functionally skipped
        # The function is called, but the output is just filled with 0s
        logger.debug("Performing placement and routing...")
    placed = place_and_route(shards, machine)
    # safety check: never run with parallelization on a 1 qubit circuit
    if machine and len(circuit.qubits) > 1:
        phir_json = genphir_parallel(placed, circuit, machine)
    else:
        phir_json = genphir(placed, circuit, machine_ops=bool(machine))
    if logger.getEffectiveLevel() <= logging.INFO:
        print("PHIR JSON:")
        print(PHIRModel.model_validate_json(phir_json))
    return phir_json


def qasm_to_phir(
    qasm: str,
    qtm_machine: QtmMachine | None = None,
    wasm_bytes: bytes | None = None,
) -> str:
    """Converts a QASM circuit string into its PHIR representation.

    This can optionally include rebasing against a Quantinuum machine architecture,
    and control of the TKET optimization level.

    :param qasm: QASM input to be converted
    :param qtm_machine: (Optional) Quantinuum machine architecture to rebase against
    :param wasm_bytes: (Optional) WASM as bytes to include as part of circuit
    """
    circuit: Circuit
    if wasm_bytes:
        with (
            NamedTemporaryFile(suffix=".qasm", delete=False) as qasm_file,
            NamedTemporaryFile(suffix=".wasm", delete=False) as wasm_file,
        ):
            qasm_file.write(qasm.encode())
            qasm_file.flush()
            wasm_file.write(wasm_bytes)
            wasm_file.flush()

            circuit = circuit_from_qasm_wasm(
                qasm_file.name, wasm_file.name, maxwidth=WORDSIZE
            )
    else:
        circuit = circuit_from_qasm_str(qasm, maxwidth=WORDSIZE)
    return pytket_to_phir(circuit, qtm_machine)
