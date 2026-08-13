"""intent_fidelity — pre-boundary intent-fidelity measurement primitive.

Part of the Remnant Fieldworks / Coherent Inheritance Framework (CIF) /
ExecutionProof program. Measures whether a model's *proposed action* still
faithfully represents the human's *authenticated request* BEFORE that action
reaches the ExecutionProof ALLOW/HOLD/DENY boundary.

Governing doctrine (from the Derek/Greg exchange, Aug 2026):
    Preserve human intent without replacing human judgment.
    Detect divergence (value-neutral); NEVER adjudicate desirability.

HONEST SCOPE: the shipped experiments run on a synthetic, de-identified corpus
with ground-truth labels. They validate the divergence primitive and its
preregistered thresholds on controlled data. They are NOT a live-LLM study and
make no claim about any deployed model's drift rate.
"""

from .ifdv import (
    AUTHORITY_LADDER,
    AXES,
    DEFAULT_TAU,
    Envelope,
    authority_escalation,
    authority_level,
    consequence_shift,
    divergence_score,
    ifdv,
    is_material,
    objective_substitution,
    scope_expansion,
)
from .metrics import (
    CHANCE_AUC,
    FAIL,
    HOLD,
    PASS,
    confusion,
    detection_verdict,
    false_positive_rate,
    f1,
    intrusion_verdict,
    meta_integrity_verdict,
    precision,
    recall,
    roc_auc,
    roc_points,
    separation_verdict,
)
from .corpus import CONSEQUENCE_WEIGHTS, SYNONYMS, Item, build_corpus
from .adjudication import (
    AdjItem,
    adjudication_leakage,
    build_adjudication_corpus,
    paternalistic_baseline_flags,
)
from .meta_integrity import (
    default_policy,
    hashing_is_deterministic,
    is_material_under,
    policy_hash,
    run_equivalence_battery,
    run_tamper_battery,
    silent_damage,
)
from .proofrecord import (
    HONEST_SCOPE,
    SERIES,
    compute_record_hash,
    load_record,
    make_proofrecord,
    save_record,
    utc_now,
    verify_record,
)

__version__ = "0.1.0a1"

__all__ = [
    "__version__",
    # ifdv
    "AUTHORITY_LADDER",
    "AXES",
    "DEFAULT_TAU",
    "Envelope",
    "authority_escalation",
    "authority_level",
    "consequence_shift",
    "divergence_score",
    "ifdv",
    "is_material",
    "objective_substitution",
    "scope_expansion",
    # metrics
    "CHANCE_AUC",
    "PASS",
    "FAIL",
    "HOLD",
    "confusion",
    "detection_verdict",
    "false_positive_rate",
    "f1",
    "intrusion_verdict",
    "meta_integrity_verdict",
    "precision",
    "recall",
    "roc_auc",
    "roc_points",
    "separation_verdict",
    # corpus
    "CONSEQUENCE_WEIGHTS",
    "SYNONYMS",
    "Item",
    "build_corpus",
    # adjudication (IF-03)
    "AdjItem",
    "adjudication_leakage",
    "build_adjudication_corpus",
    "paternalistic_baseline_flags",
    # meta-integrity (IF-05)
    "default_policy",
    "hashing_is_deterministic",
    "is_material_under",
    "policy_hash",
    "run_equivalence_battery",
    "run_tamper_battery",
    "silent_damage",
    # proofrecord
    "HONEST_SCOPE",
    "SERIES",
    "compute_record_hash",
    "load_record",
    "make_proofrecord",
    "save_record",
    "utc_now",
    "verify_record",
]
