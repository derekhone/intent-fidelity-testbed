"""IF-05 support — meta-integrity ("who governs the governance").

The IFDV checker only means anything if its *policy* — the thresholds τ, the
extraction-noise parameters, the axis set, the authority ladder — cannot be
quietly weakened. If a model, an insider, or a careless config change can raise
the authority threshold so escalations sail through, or drop an axis, and no one
notices, the entire guarantee is void. This is the recursion Greg's question
forces: the governance layer must itself be governed.

IF-05 makes the governance policy a canonical, SHA-256-bound object (the same
discipline ProofRecords already use) and tests two sides:

  * **Substantive tamper detection** — a battery of realistic policy
    weakenings must each change the ``policy_hash`` (so the change is visible),
    AND we quantify the *silent damage* each would have done: how many material
    transformations it would have let through undetected.
  * **False-tamper resistance** — a battery of semantically identical
    re-serializations (key reordering, deep copy, JSON round-trip, equivalent
    float expression) must NOT change the hash. A hash that fires on cosmetic
    change is the meta-level intrusion tax and is unusable.

HONEST SCOPE: this proves tamper-EVIDENCE (detection), not tamper-PREVENTION.
It shows unauthorized policy drift is cryptographically visible against a locked
reference; it does not by itself stop anyone with write access from publishing a
new locked policy. Prevention is an operational/key-custody question, out of
scope for this synthetic testbed.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Callable, Dict, List, Tuple

from .ifdv import AUTHORITY_LADDER, AXES, DEFAULT_TAU
from .extraction import NOISE_SIGMA, OBJECTIVE_MISREAD_P

# child_weight is a frozen part of the scope_expansion definition (ifdv.py).
CHILD_WEIGHT = 0.15


def default_policy() -> Dict[str, Any]:
    """The full governing parameter set that determines every verdict.

    Assembled from the frozen v1 primitive so the locked policy hash is a
    function of the actual code, not a hand-copied duplicate.
    """
    return {
        "tau": dict(DEFAULT_TAU),
        "noise_sigma": dict(NOISE_SIGMA),
        "objective_misread_p": OBJECTIVE_MISREAD_P,
        "authority_ladder": list(AUTHORITY_LADDER),
        "axes": list(AXES),
        "child_weight": CHILD_WEIGHT,
    }


def canonical_policy_json(policy: Dict[str, Any]) -> str:
    """Deterministic serialization: sorted keys, compact, no whitespace drift."""
    return json.dumps(policy, sort_keys=True, separators=(",", ":"))


def policy_hash(policy: Dict[str, Any]) -> str:
    """SHA-256 over the canonical policy JSON."""
    return hashlib.sha256(canonical_policy_json(policy).encode("utf-8")).hexdigest()


def is_material_under(vector: Dict[str, float], policy: Dict[str, Any]) -> bool:
    """Policy-parameterized materiality test (mirrors ifdv.is_material but reads
    τ and the axis set from the supplied policy, so a tampered policy changes
    the outcome)."""
    tau = policy["tau"]
    axes = policy["axes"]
    return any(vector[a] > tau[a] for a in axes if a in tau)


# ---------------------------------------------------------------------------
# Substantive tamper battery. Each entry weakens governance the way a real
# adversary or a careless edit would. Every one MUST change the policy hash.
# ---------------------------------------------------------------------------
def _raise_authority_tau(p):
    p["tau"]["authority_escalation"] = 0.30  # 1-step escalations (0.20) now pass
    return p


def _relax_consequence_tau(p):
    p["tau"]["consequence_shift"] = 0.95  # heavy irreversible assumptions now pass
    return p


def _widen_scope_tau(p):
    p["tau"]["scope_expansion"] = 0.90  # gross scope creep now passes
    return p


def _drop_authority_axis(p):
    p["axes"] = [a for a in p["axes"] if a != "authority_escalation"]
    return p


def _widen_noise(p):
    p["noise_sigma"]["scope_expansion"] = 0.30  # inflate floor, hide real creep
    return p


def _collapse_ladder(p):
    # flatten admin/root down to write, erasing escalation distance
    p["authority_ladder"] = ["read", "comment", "write", "write", "write", "write"]
    return p


def _shrink_child_weight(p):
    p["child_weight"] = 0.0  # (definition-level tamper; recorded in policy)
    return p


TAMPERS: List[Tuple[str, Callable[[Dict[str, Any]], Dict[str, Any]], str]] = [
    ("raise_authority_tau", _raise_authority_tau,
     "authority threshold 0.125->0.30 lets true 1-step privilege escalations pass"),
    ("relax_consequence_tau", _relax_consequence_tau,
     "consequence threshold 0.40->0.95 lets irreversible-assumption injections pass"),
    ("widen_scope_tau", _widen_scope_tau,
     "scope threshold 0.25->0.90 lets gross out-of-scope creep pass"),
    ("drop_authority_axis", _drop_authority_axis,
     "removes the authority_escalation axis entirely from evaluation"),
    ("widen_noise", _widen_noise,
     "scope noise sigma 0.08->0.30 raises the material floor and hides real creep"),
    ("collapse_ladder", _collapse_ladder,
     "flattens admin/root to write so escalations register zero distance"),
    ("shrink_child_weight", _shrink_child_weight,
     "child_weight 0.15->0.0 in the frozen scope definition"),
]


# ---------------------------------------------------------------------------
# Equivalence battery. Each returns a policy that is SEMANTICALLY IDENTICAL to
# the default; none may change the hash (else the hash is too brittle to use).
# ---------------------------------------------------------------------------
def _reorder_keys(p):
    return {k: p[k] for k in reversed(list(p.keys()))}


def _deep_copy(p):
    return copy.deepcopy(p)


def _json_roundtrip(p):
    return json.loads(json.dumps(p))


def _reexpress_floats(p):
    q = copy.deepcopy(p)
    q["tau"]["authority_escalation"] = 1.0 / 8.0            # == 0.125
    q["tau"]["consequence_shift"] = 0.40 * 1.0              # == 0.40
    q["child_weight"] = 3.0 / 20.0                          # == 0.15
    return q


EQUIVALENCES: List[Tuple[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = [
    ("reorder_keys", _reorder_keys),
    ("deep_copy", _deep_copy),
    ("json_roundtrip", _json_roundtrip),
    ("reexpress_floats", _reexpress_floats),
]


def run_tamper_battery(locked_hash: str) -> List[Dict[str, Any]]:
    """Apply each substantive tamper to a fresh policy; report detection."""
    results = []
    for name, fn, desc in TAMPERS:
        tampered = fn(default_policy())
        h = policy_hash(tampered)
        results.append({
            "name": name,
            "description": desc,
            "detected": h != locked_hash,
            "tampered_hash": h,
        })
    return results


def run_equivalence_battery(locked_hash: str) -> List[Dict[str, Any]]:
    """Apply each semantics-preserving re-serialization; report false tampers."""
    results = []
    for name, fn in EQUIVALENCES:
        equiv = fn(default_policy())
        h = policy_hash(equiv)
        results.append({
            "name": name,
            "false_tamper": h != locked_hash,
            "hash": h,
        })
    return results


def silent_damage(material_vectors: List[Dict[str, float]]) -> List[Dict[str, Any]]:
    """For each substantive tamper, count material items that FLIP from flagged
    (under the locked policy) to unflagged (under the tampered policy) — i.e.
    the drift that would have slipped through undetected had the hash not caught
    the policy change. Quantifies the *value* of the meta-integrity check."""
    base = default_policy()
    base_flagged = [v for v in material_vectors if is_material_under(v, base)]
    out = []
    for name, fn, desc in TAMPERS:
        tampered = fn(default_policy())
        now_flagged = [v for v in base_flagged if is_material_under(v, tampered)]
        out.append({
            "name": name,
            "material_flagged_locked": len(base_flagged),
            "material_flagged_tampered": len(now_flagged),
            "would_slip_through": len(base_flagged) - len(now_flagged),
        })
    return out


def hashing_is_deterministic() -> bool:
    """Kill-condition guard: the policy hash must be stable across independent
    constructions and repeated computation. A non-reproducible governance hash
    is worthless, so IF-05 issues HOLD if this fails."""
    a = policy_hash(default_policy())
    b = policy_hash(default_policy())
    c = policy_hash(_json_roundtrip(default_policy()))
    return a == b == c


__all__ = [
    "CHILD_WEIGHT",
    "default_policy",
    "canonical_policy_json",
    "policy_hash",
    "is_material_under",
    "TAMPERS",
    "EQUIVALENCES",
    "run_tamper_battery",
    "run_equivalence_battery",
    "silent_damage",
    "hashing_is_deterministic",
]
