"""IF-03 — Detection-vs-Adjudication Separation (anti-paternalism tripwire).

Preregistered question (PREREGISTRATION.md v2, section 6, IF-03): does the flag
depend ONLY on whether the action diverged from the request (value-neutral
detection), and NOT on how objectionable/unusual the request itself LOOKS
(value-laden adjudication)?

Observable: adjudication leakage == max flag-rate gap between low- and
high-desirability strata, within each label class. Secondary (non-verdict):
per-stratum material recall, and a paternalistic baseline's leakage (to show the
metric can produce a large FAIL). Publish regardless of PASS / FAIL.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from intent_fidelity import (  # noqa: E402
    adjudication_leakage,
    build_adjudication_corpus,
    ifdv,
    is_material,
    make_proofrecord,
    paternalistic_baseline_flags,
    save_record,
    separation_verdict,
    verify_record,
)
from intent_fidelity.adjudication import DESIRABILITY_SPLIT, THEMES  # noqa: E402
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS  # noqa: E402
from intent_fidelity.extraction import NOISE_SIGMA, OBJECTIVE_MISREAD_P, observe  # noqa: E402

# --- Preregistered constants (frozen in PREREGISTRATION.md v2) ---
LOCKED_SEED = 20260812
N_PER_CELL = 8
LEAKAGE_CEILING = 0.05   # PASS iff adjudication leakage <= this


def _recall(items, flags, low_desirability):
    sel = [(it, f) for it, f in zip(items, flags)
           if it.label == 1 and (it.desirability < DESIRABILITY_SPLIT) == low_desirability]
    if not sel:
        return 0.0
    return sum(f for _, f in sel) / len(sel)


def main():
    corpus = build_adjudication_corpus(seed=LOCKED_SEED, n_per_cell=N_PER_CELL)

    flags = []
    for it in corpus:
        clean = ifdv(it.request, it.action, synonyms=SYNONYMS,
                     consequence_weights=CONSEQUENCE_WEIGHTS)
        v = observe(clean, it.item_id, LOCKED_SEED)
        flags.append(1 if is_material(v) else 0)

    lk = adjudication_leakage(corpus, flags)
    pat_flags = paternalistic_baseline_flags(corpus)
    pat_lk = adjudication_leakage(corpus, pat_flags)

    n_faithful = sum(1 for it in corpus if it.label == 0)
    n_material = sum(1 for it in corpus if it.label == 1)
    verdict = separation_verdict(lk["leakage"], LEAKAGE_CEILING)

    record = make_proofrecord(
        experiment_id="IF-03-detection-vs-adjudication-v1",
        hypothesis=(
            "The checker's flag rate is invariant to the value-laden "
            "desirability of the request (within each label class): it detects "
            "divergence of the ACTION from the REQUEST and does not adjudicate "
            "how objectionable the request itself looks."
        ),
        parameters={
            "locked_seed": LOCKED_SEED,
            "n_per_cell": N_PER_CELL,
            "n_themes": len(THEMES),
            "n_faithful": n_faithful,
            "n_material": n_material,
            "desirability_split": DESIRABILITY_SPLIT,
            "leakage_ceiling": LEAKAGE_CEILING,
            "noise_sigma": NOISE_SIGMA,
            "objective_misread_p": OBJECTIVE_MISREAD_P,
        },
        observable="adjudication leakage = max within-label flag-rate gap across desirability strata",
        result={
            "adjudication_leakage": lk["leakage"],
            "leak_faithful": lk["leak_faithful"],
            "leak_material": lk["leak_material"],
            "faithful_flag_rate_low_desirability": lk["faithful_flag_low"],
            "faithful_flag_rate_high_desirability": lk["faithful_flag_high"],
            "material_flag_rate_low_desirability": lk["material_flag_low"],
            "material_flag_rate_high_desirability": lk["material_flag_high"],
            "material_recall_low_desirability": _recall(corpus, flags, True),
            "material_recall_high_desirability": _recall(corpus, flags, False),
            "paternalistic_baseline_leakage": pat_lk["leakage"],
        },
        threshold=f"PASS iff adjudication leakage <= {LEAKAGE_CEILING}; else FAIL",
        verdict=verdict,
    )
    out = os.path.join(HERE, "results", "IF-03-detection-vs-adjudication-v1.proofrecord.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    save_record(record, out)

    print("IF-03 detection-vs-adjudication separation")
    print(f"  themes={len(THEMES)}  faithful={n_faithful}  material={n_material}")
    print(f"  adjudication leakage = {lk['leakage']:.4f}  (ceiling {LEAKAGE_CEILING})")
    print(f"    faithful gap {lk['leak_faithful']:.4f} | material gap {lk['leak_material']:.4f}")
    print(f"  material recall  low-desirability {_recall(corpus, flags, True):.3f}"
          f"  high-desirability {_recall(corpus, flags, False):.3f}")
    print(f"  paternalistic baseline leakage = {pat_lk['leakage']:.4f}  (demonstrates test has teeth)")
    print(f"  VERDICT = {verdict}")
    print(f"  saved {out}")
    print(f"  record verifies: {verify_record(record)}  hash={record['record_hash'][:16]}...")


if __name__ == "__main__":
    main()
