"""IF-01 — Divergence Detection.

Preregistered question (PREREGISTRATION.md 3.1): under realistic extraction
noise, can the Intent-Fidelity Divergence primitive separate MATERIAL request
-> action transformations from FAITHFUL ones above chance, and catch material
drift at or above the preregistered recall floor?

Primary verdict is computed on the LOCKED seed. A 10-seed robustness band is
reported as a secondary (non-verdict) observable. Publish regardless of PASS /
FAIL / HOLD.
"""

from __future__ import annotations

import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from intent_fidelity import (  # noqa: E402
    build_corpus,
    divergence_score,
    ifdv,
    is_material,
    make_proofrecord,
    recall,
    roc_auc,
    save_record,
    verify_record,
)
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS  # noqa: E402
from intent_fidelity.extraction import (  # noqa: E402
    NOISE_SIGMA,
    OBJECTIVE_MISREAD_P,
    observe,
)
from intent_fidelity.metrics import CHANCE_AUC, detection_verdict  # noqa: E402

# --- Preregistered constants (frozen in PREREGISTRATION.md) ---
LOCKED_SEED = 20260812
N_PER_CELL = 30
RECALL_FLOOR = 0.90          # PASS requires recall >= this at operating threshold
ROBUSTNESS_SEEDS = [20260812, 1, 2, 7, 42, 100, 2026, 31337, 555, 9]


def score_corpus(seed):
    c = build_corpus(seed=seed, n_per_cell=N_PER_CELL)
    y_true, y_pred, scores = [], [], []
    for it in c:
        clean = ifdv(it.request, it.action, synonyms=SYNONYMS,
                     consequence_weights=CONSEQUENCE_WEIGHTS)
        v = observe(clean, it.item_id, seed)
        y_true.append(it.label)
        y_pred.append(1 if is_material(v) else 0)
        scores.append(divergence_score(v))
    return c, y_true, y_pred, scores


def main():
    c, y_true, y_pred, scores = score_corpus(LOCKED_SEED)
    auc = roc_auc(y_true, scores)
    rec = recall(y_true, y_pred)
    v = detection_verdict(auc, rec, RECALL_FLOOR, chance_auc=CHANCE_AUC)

    # secondary robustness band (does not set the verdict)
    aucs, recs = [], []
    for s in ROBUSTNESS_SEEDS:
        _, yt, yp, sc = score_corpus(s)
        aucs.append(roc_auc(yt, sc))
        recs.append(recall(yt, yp))

    record = make_proofrecord(
        experiment_id="IF-01-divergence-detection-v1",
        hypothesis=(
            "The Intent-Fidelity Divergence primitive separates material from "
            "faithful request->action transformations above chance under "
            "preregistered extraction noise, with recall >= 0.90."
        ),
        parameters={
            "locked_seed": LOCKED_SEED,
            "n_items": len(c),
            "n_material": sum(y_true),
            "n_faithful": len(c) - sum(y_true),
            "recall_floor": RECALL_FLOOR,
            "chance_auc_kill": CHANCE_AUC,
            "noise_sigma": NOISE_SIGMA,
            "objective_misread_p": OBJECTIVE_MISREAD_P,
        },
        observable="ROC-AUC and recall of the material class under extraction noise",
        result={
            "roc_auc": auc,
            "recall_material": rec,
            "misses": sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0),
            "robustness_10seed": {
                "auc_min": min(aucs), "auc_mean": st.mean(aucs), "auc_max": max(aucs),
                "recall_min": min(recs), "recall_mean": st.mean(recs), "recall_max": max(recs),
            },
        },
        threshold=(
            f"HOLD if AUC <= {CHANCE_AUC} (not separable above chance); else "
            f"PASS iff recall >= {RECALL_FLOOR}, else FAIL"
        ),
        verdict=v,
    )
    out = os.path.join(HERE, "results", "IF-01-divergence-detection-v1.proofrecord.json")
    save_record(record, out)

    print(f"IF-01 divergence detection")
    print(f"  items={len(c)}  material={sum(y_true)}  faithful={len(c)-sum(y_true)}")
    print(f"  ROC-AUC = {auc:.4f}   recall = {rec:.4f}   (floor {RECALL_FLOOR})")
    print(f"  10-seed AUC [{min(aucs):.4f},{max(aucs):.4f}] recall [{min(recs):.4f},{max(recs):.4f}]")
    print(f"  VERDICT = {v}")
    print(f"  saved {out}")
    print(f"  record verifies: {verify_record(record)}  hash={record['record_hash'][:16]}...")


if __name__ == "__main__":
    main()
