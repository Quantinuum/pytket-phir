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

Requires Python ``>=3.12, <3.16``.

To install pytket-phir, simply run:

.. code-block:: bash

   pip install pytket-phir

For the optional ``phirc`` CLI:

.. code-block:: bash

   pip install "pytket-phir[phirc]"

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
