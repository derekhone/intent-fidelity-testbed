"""Imperfect-extraction (observation) model for the intent-fidelity primitive.

In a real deployment the checker never receives perfectly structured envelopes.
It must EXTRACT objective / scope / authority / assumptions from the raw
request and the model's proposed action, and that extraction is imperfect. A
testbed that scored the primitive on perfectly clean structure would return a
trivially perfect result and prove nothing.

So we model extraction noise explicitly and PREREGISTER it (see
PREREGISTRATION.md section 2.1). Given the clean, ground-truth IFDV for an
item, ``observe`` returns the NOISY IFDV the detector actually sees. Noise is
seeded per item, so every ProofRecord is exactly reproducible from source.

The point of IF-01 / IF-02 is precisely whether the divergence primitive and
its thresholds remain useful UNDER this realistic extraction noise — high
recall on material drift without an unacceptable intrusion tax.
"""

from __future__ import annotations

import random
from typing import Dict

from .ifdv import AXES

# Preregistered per-axis extraction-noise parameters (frozen in
# PREREGISTRATION.md 2.1). Gaussian additive noise for the graded axes; a
# discrete misread probability for the binary objective axis.
NOISE_SIGMA: Dict[str, float] = {
    "scope_expansion": 0.08,
    "authority_escalation": 0.05,
    "consequence_shift": 0.08,
}
OBJECTIVE_MISREAD_P: float = 0.03  # prob a paraphrase/substitution is misread


def observe(clean: Dict[str, float], item_id: str, seed: int) -> Dict[str, float]:
    """Return the noisy IFDV the detector observes for one item.

    Deterministic given (item_id, seed): the per-item RNG is seeded from the
    hash of both, so re-running reproduces identical observations and thus
    identical ProofRecords.
    """
    rng = random.Random(f"{seed}:{item_id}")
    observed: Dict[str, float] = {}
    for axis in AXES:
        val = clean[axis]
        if axis == "objective_substitution":
            # binary axis: with small prob the extractor flips the read
            if rng.random() < OBJECTIVE_MISREAD_P:
                val = 1.0 - val
            observed[axis] = val
        else:
            noisy = val + rng.gauss(0.0, NOISE_SIGMA[axis])
            observed[axis] = min(1.0, max(0.0, noisy))
    return observed


__all__ = ["NOISE_SIGMA", "OBJECTIVE_MISREAD_P", "observe"]
