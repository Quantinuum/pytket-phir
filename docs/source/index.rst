pytket-phir
===========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

PHIR stands for `PECOS <https://github.com/PECOS-packages/PECOS>`__
*High-level Intermediate Representation*. See `PHIR
specification <https://github.com/quantinuum/phir/blob/main/spec.md>`__
for more.

``pytket-phir`` is a circuit analyzer and translator from
`pytket <https://tket.quantinuum.com/api-docs/index.html>`__ to PHIR.

Also included is the CLI tool ``phirc`` that takes QASM programs as
input and emulates them using PECOS.

Installation
------------

Python 3.12–3.15 is supported. CI tests these versions on Linux and Windows.

CI tests circuit translation and optional ``phirc`` emulation using the locked
dependencies. To use that environment from a checkout, run
``uv sync --extra phirc``. The lockfile selects PECOS ``0.8.0.dev0`` without
Guppy, HUGR, or Selene; ``pip`` installs may select newer PECOS releases.

To install pytket-phir, simply run:

.. code-block:: bash

   pip install pytket-phir

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
