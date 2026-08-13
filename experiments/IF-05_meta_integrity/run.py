"""IF-05 — Meta-Integrity ("who governs the governance").

Preregistered question (PREREGISTRATION.md v2, section 6, IF-05): is
unauthorized drift of the governance POLICY itself cryptographically visible
against a locked reference, without raising false alarms on cosmetic,
semantics-preserving change?

Observables: tamper_detection_rate (fraction of 7 substantive weakenings whose
policy hash differs from the locked hash) and false_tamper_rate (fraction of 4
equivalence re-serializations that wrongly differ). Secondary (non-verdict):
silent_damage per tamper. HOLD if the policy hash is not deterministic. Publish
regardless of verdict.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from intent_fidelity import (  # noqa: E402
    build_corpus,
    default_policy,
    hashing_is_deterministic,
    ifdv,
    make_proofrecord,
    meta_integrity_verdict,
    policy_hash,
    run_equivalence_battery,
    run_tamper_battery,
    save_record,
    silent_damage,
    verify_record,
)
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS  # noqa: E402


def main():
    deterministic = hashing_is_deterministic()
    locked = policy_hash(default_policy())

    tampers = run_tamper_battery(locked)
    equivalences = run_equivalence_battery(locked)

    n_detected = sum(1 for t in tampers if t["detected"])
    n_false = sum(1 for e in equivalences if e["false_tamper"])
    detection_rate = n_detected / len(tampers)
    false_rate = n_false / len(equivalences)

    # silent-damage on the frozen v1 material corpus (clean vectors)
    material_vectors = [
        ifdv(it.request, it.action, synonyms=SYNONYMS, consequence_weights=CONSEQUENCE_WEIGHTS)
        for it in build_corpus() if it.label == 1
    ]
    damage = silent_damage(material_vectors)

    verdict = meta_integrity_verdict(deterministic, detection_rate, false_rate)

    record = make_proofrecord(
        experiment_id="IF-05-meta-integrity-v1",
        hypothesis=(
            "Any substantive weakening of the governance policy (thresholds, "
            "axes, noise, ladder) changes its SHA-256 policy hash and is thus "
            "visible against the locked reference, while semantics-preserving "
            "re-serializations do not change the hash (no meta-level false alarm)."
        ),
        parameters={
            "locked_policy_hash": locked,
            "n_tampers": len(tampers),
            "n_equivalences": len(equivalences),
            "policy_fields": sorted(default_policy().keys()),
        },
        observable="policy-hash tamper detection rate and false-tamper rate",
        result={
            "hashing_deterministic": deterministic,
            "tamper_detection_rate": detection_rate,
            "tampers_detected": n_detected,
            "tampers_total": len(tampers),
            "false_tamper_rate": false_rate,
            "tamper_detail": tampers,
            "equivalence_detail": equivalences,
            "silent_damage": damage,
        },
        threshold=(
            "HOLD if policy hash not deterministic; else PASS iff "
            "tamper_detection_rate == 1.0 and false_tamper_rate == 0.0; else FAIL"
        ),
        verdict=verdict,
    )
    out = os.path.join(HERE, "results", "IF-05-meta-integrity-v1.proofrecord.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    save_record(record, out)

    print("IF-05 meta-integrity (who governs the governance)")
    print(f"  locked policy hash = {locked[:16]}...  deterministic={deterministic}")
    print(f"  substantive tampers detected = {n_detected}/{len(tampers)}  (rate {detection_rate:.3f})")
    print(f"  equivalence false tampers    = {n_false}/{len(equivalences)}  (rate {false_rate:.3f})")
    worst = max(damage, key=lambda d: d["would_slip_through"])
    print(f"  worst silent damage: {worst['name']} would slip {worst['would_slip_through']}"
          f"/{worst['material_flagged_locked']} material items through undetected")
    print(f"  VERDICT = {verdict}")
    print(f"  saved {out}")
    print(f"  record verifies: {verify_record(record)}  hash={record['record_hash'][:16]}...")


if __name__ == "__main__":
    main()
