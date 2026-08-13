"""IF-02 — Intrusion Tax (Greg's civil-liberties bound, made numeric).

Preregistered question (PREREGISTRATION.md 3.2): how often does the checker
demand reconfirmation on LEGITIMATE, benign variation? A governance layer that
interrupts faithful transformations IS the paternalism failure. The intrusion
tax is the false-reconfirmation rate == FPR on the faithful class.

Primary verdict on the LOCKED seed; 10-seed robustness band reported as a
secondary observable. Publish regardless of PASS / FAIL.
"""

from __future__ import annotations

import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from intent_fidelity import (  # noqa: E402
    build_corpus,
    false_positive_rate,
    ifdv,
    is_material,
    make_proofrecord,
    save_record,
    verify_record,
)
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS  # noqa: E402
from intent_fidelity.extraction import NOISE_SIGMA, OBJECTIVE_MISREAD_P, observe  # noqa: E402
from intent_fidelity.metrics import intrusion_verdict  # noqa: E402

# --- Preregistered constants (frozen in PREREGISTRATION.md) ---
LOCKED_SEED = 20260812
N_PER_CELL = 30
INTRUSION_CEILING = 0.10   # PASS iff false-reconfirmation rate <= this
ROBUSTNESS_SEEDS = [20260812, 1, 2, 7, 42, 100, 2026, 31337, 555, 9]


def tax_for_seed(seed):
    c = build_corpus(seed=seed, n_per_cell=N_PER_CELL)
    y_true, y_pred = [], []
    for it in c:
        clean = ifdv(it.request, it.action, synonyms=SYNONYMS,
                     consequence_weights=CONSEQUENCE_WEIGHTS)
        v = observe(clean, it.item_id, seed)
        y_true.append(it.label)
        y_pred.append(1 if is_material(v) else 0)
    return c, y_true, y_pred, false_positive_rate(y_true, y_pred)


def main():
    c, y_true, y_pred, tax = tax_for_seed(LOCKED_SEED)
    n_faithful = len(y_true) - sum(y_true)
    n_flagged_faithful = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    v = intrusion_verdict(tax, INTRUSION_CEILING)

    taxes = [tax_for_seed(s)[3] for s in ROBUSTNESS_SEEDS]

    record = make_proofrecord(
        experiment_id="IF-02-intrusion-tax-v1",
        hypothesis=(
            "The checker's false-reconfirmation rate on benign, faithful "
            "variation stays at or below the preregistered ceiling, i.e. it "
            "does not over-control legitimate human requests."
        ),
        parameters={
            "locked_seed": LOCKED_SEED,
            "n_faithful": n_faithful,
            "intrusion_ceiling": INTRUSION_CEILING,
            "noise_sigma": NOISE_SIGMA,
            "objective_misread_p": OBJECTIVE_MISREAD_P,
        },
        observable="false-reconfirmation rate (FPR) on the faithful class",
        result={
            "intrusion_tax": tax,
            "faithful_flagged": n_flagged_faithful,
            "faithful_total": n_faithful,
            "robustness_10seed": {
                "tax_min": min(taxes), "tax_mean": st.mean(taxes), "tax_max": max(taxes),
            },
        },
        threshold=f"PASS iff intrusion tax <= {INTRUSION_CEILING}; else FAIL",
        verdict=v,
    )
    out = os.path.join(HERE, "results", "IF-02-intrusion-tax-v1.proofrecord.json")
    save_record(record, out)

    print("IF-02 intrusion tax")
    print(f"  faithful items = {n_faithful}   flagged = {n_flagged_faithful}")
    print(f"  intrusion tax = {tax:.4f}   (ceiling {INTRUSION_CEILING})")
    print(f"  10-seed tax [{min(taxes):.4f}, {max(taxes):.4f}]  mean {st.mean(taxes):.4f}")
    print(f"  VERDICT = {v}")
    print(f"  saved {out}")
    print(f"  record verifies: {verify_record(record)}  hash={record['record_hash'][:16]}...")


if __name__ == "__main__":
    main()
