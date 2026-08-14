"""IF-04 — Reconfirmation Efficacy.

Preregistered question (PREREGISTRATION.md v3, IF-04): when the IFDV checker
correctly flags a material transformation for reconfirmation, does the
divergence vector provide *actionable* information — does its dominant axis
correctly identify the TYPE of divergence that occurred, so the human knows
what to look at?

Without accurate axis attribution, the reconfirmation prompt degenerates into
a generic "are you sure?" and the human cannot make an informed decision.
Accurate attribution makes the difference between detection-as-information
(human reads "authority was escalated from write to admin") and
detection-as-obstruction (human reads "something changed, approve?").

Observable: axis attribution accuracy = fraction of true positives where the
dominant IFDV axis matches the ground-truth divergence category.
Secondary: false-alarm axis profile — which axis drives false positives (so
misleading reconfirmation messages can be assessed).

HONEST SCOPE: synthetic corpus with ground-truth labels; validates the
*actionability* of the IFDV output, not a live human reconfirmation study.
"""

from __future__ import annotations

import os
import sys
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from intent_fidelity import (  # noqa: E402
    build_corpus,
    divergence_score,
    ifdv,
    is_material,
    make_proofrecord,
    save_record,
    verify_record,
)
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS  # noqa: E402
from intent_fidelity.extraction import observe  # noqa: E402
from intent_fidelity.ifdv import AXES, DEFAULT_TAU  # noqa: E402

# --- Preregistered constants ---
LOCKED_SEED = 20260812
N_PER_CELL = 30
ATTRIBUTION_FLOOR = 0.80     # PASS requires >= 80% correct axis attribution
RECALL_KILL = 0.60            # HOLD if not enough TPs to measure attribution
ROBUSTNESS_SEEDS = [20260812, 1, 2, 7, 42, 100, 2026, 31337, 555, 9]

# Ground-truth mapping: corpus category -> expected dominant IFDV axis
CATEGORY_TO_AXIS = {
    "material.scope_creep": "scope_expansion",
    "material.scope_creep.subtle": "scope_expansion",
    "material.objective_swap": "objective_substitution",
    "material.objective_swap.subtle": "objective_substitution",
    "material.authority_escalation": "authority_escalation",
    "material.authority_escalation.subtle": "authority_escalation",
    "material.consequence_injection": "consequence_shift",
    "material.consequence_injection.subtle": "consequence_shift",
}


def dominant_axis(vector, tau=None):
    """Return the axis with the highest normalized divergence (axis/tau)."""
    tau = tau or DEFAULT_TAU
    return max(AXES, key=lambda a: vector[a] / tau[a])


def score_attribution(seed):
    """Score axis attribution accuracy on true positives."""
    corpus = build_corpus(seed=seed, n_per_cell=N_PER_CELL)
    tp_correct = 0
    tp_total = 0
    fp_axis_counts = {a: 0 for a in AXES}
    fp_total = 0
    recall_denom = sum(1 for it in corpus if it.label == 1)
    recall_numer = 0

    for it in corpus:
        clean = ifdv(it.request, it.action, synonyms=SYNONYMS,
                     consequence_weights=CONSEQUENCE_WEIGHTS)
        v = observe(clean, it.item_id, seed)
        flagged = is_material(v)

        if it.label == 1 and flagged:
            # True positive — check axis attribution
            recall_numer += 1
            dom = dominant_axis(v)
            expected = CATEGORY_TO_AXIS.get(it.category)
            if expected and dom == expected:
                tp_correct += 1
            tp_total += 1
        elif it.label == 0 and flagged:
            # False positive — record which axis drove the false alarm
            dom = dominant_axis(v)
            fp_axis_counts[dom] += 1
            fp_total += 1

    rec = recall_numer / recall_denom if recall_denom > 0 else 0.0
    acc = tp_correct / tp_total if tp_total > 0 else 0.0
    return {
        "attribution_accuracy": acc,
        "tp_correct": tp_correct,
        "tp_total": tp_total,
        "recall": rec,
        "fp_total": fp_total,
        "fp_axis_profile": fp_axis_counts,
    }


def main():
    primary = score_attribution(LOCKED_SEED)
    acc = primary["attribution_accuracy"]
    rec = primary["recall"]

    # Kill condition: not enough TPs
    if rec < RECALL_KILL:
        verdict = "HOLD"
    elif acc >= ATTRIBUTION_FLOOR:
        verdict = "PASS"
    else:
        verdict = "FAIL"

    # Secondary: robustness band
    rob_accs = []
    for s in ROBUSTNESS_SEEDS:
        r = score_attribution(s)
        rob_accs.append(r["attribution_accuracy"])

    record = make_proofrecord(
        experiment_id="IF-04-reconfirmation-efficacy-v1",
        hypothesis=(
            "When the IFDV checker correctly flags a material transformation, "
            "the dominant divergence axis matches the ground-truth category of "
            "the transformation, making the reconfirmation message actionable "
            "rather than a generic 'are you sure?' prompt."
        ),
        parameters={
            "locked_seed": LOCKED_SEED,
            "n_per_cell": N_PER_CELL,
            "attribution_floor": ATTRIBUTION_FLOOR,
            "recall_kill": RECALL_KILL,
            "category_to_axis": CATEGORY_TO_AXIS,
        },
        observable="axis attribution accuracy on true positives",
        result={
            "attribution_accuracy": acc,
            "tp_correct": primary["tp_correct"],
            "tp_total": primary["tp_total"],
            "recall": rec,
            "fp_total": primary["fp_total"],
            "fp_axis_profile": primary["fp_axis_profile"],
            "robustness_10seed": {
                "acc_min": min(rob_accs),
                "acc_mean": st.mean(rob_accs),
                "acc_max": max(rob_accs),
            },
        },
        threshold=(
            f"HOLD if recall < {RECALL_KILL}; "
            f"PASS iff axis_attribution_accuracy >= {ATTRIBUTION_FLOOR}; else FAIL"
        ),
        verdict=verdict,
    )

    out = os.path.join(HERE, "results",
                       "IF-04-reconfirmation-efficacy-v1.proofrecord.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    save_record(record, out)

    print("=" * 70)
    print("IF-04 Reconfirmation Efficacy")
    print("=" * 70)
    print(f"  attribution accuracy : {acc:.4f}  ({primary['tp_correct']}/{primary['tp_total']} TPs)")
    print(f"  recall               : {rec:.4f}")
    print(f"  false positives      : {primary['fp_total']}")
    print(f"  FP axis profile      : {primary['fp_axis_profile']}")
    print(f"  robustness (10 seed) : [{min(rob_accs):.3f}, {st.mean(rob_accs):.3f}, {max(rob_accs):.3f}]")
    print(f"  VERDICT              : {verdict}")
    print(f"  record verifies      : {verify_record(record)}")
    print(f"  hash                 : {record['record_hash'][:16]}...")
    print(f"  saved                : {out}")
    return record


if __name__ == "__main__":
    main()
