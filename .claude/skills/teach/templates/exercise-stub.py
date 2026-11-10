"""T3 — Implementation. Fill every function marked TODO. Do not change signatures.

Oracle tests: `pytest exercises/tests -q`. Cards: translate.md (C1–C<n>).
Conventions: R_proc = process noise, Q_meas = measurement noise. Wrap angles with `wrap`.
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from .models import wrap  # noqa: F401


def <function>(<args>):
    """<Book table line / equation>. Return <contract>. <One constraint, e.g. never call np.linalg.inv.>"""
    raise NotImplementedError("TODO")
