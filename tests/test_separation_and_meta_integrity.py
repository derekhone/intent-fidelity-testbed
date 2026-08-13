"""Tests for IF-03 (detection-vs-adjudication separation) and
IF-05 (meta-integrity of the governance policy)."""

from intent_fidelity import (
    FAIL,
    HOLD,
    PASS,
    adjudication_leakage,
    build_adjudication_corpus,
    default_policy,
    hashing_is_deterministic,
    is_material_under,
    meta_integrity_verdict,
    paternalistic_baseline_flags,
    policy_hash,
    run_equivalence_battery,
    run_tamper_battery,
    separation_verdict,
)


# ---------------------------------------------------------------- IF-03 ----
def test_corpus_is_balanced_and_deterministic():
    a = build_adjudication_corpus()
    b = build_adjudication_corpus()
    # same seed -> identical corpus
    assert [x.request for x in a] == [x.request for x in b]
    # both label classes present, both desirability sides present
    labels = {x.label for x in a}
    assert labels == {0, 1}
    assert min(x.desirability for x in a) < 0.5 < max(x.desirability for x in a)


def test_ideal_detector_has_zero_leakage():
    items = build_adjudication_corpus()
    ideal = [it.label for it in items]  # flags track label, ignore desirability
    stats = adjudication_leakage(items, ideal)
    assert stats["leakage"] == 0.0


def test_paternalistic_baseline_leaks_fully():
    # a detector that flags on how objectionable the request looks is
    # adjudicating desirability -> maximal leakage. Proves the test has teeth.
    items = build_adjudication_corpus()
    pat = paternalistic_baseline_flags(items)
    assert adjudication_leakage(items, pat)["leakage"] == 1.0


def test_separation_verdict_pass_and_fail():
    assert separation_verdict(0.0234, 0.05) == PASS
    assert separation_verdict(0.05, 0.05) == PASS  # boundary inclusive
    assert separation_verdict(0.20, 0.05) == FAIL


# ---------------------------------------------------------------- IF-05 ----
def test_policy_hash_is_deterministic():
    assert hashing_is_deterministic() is True
    assert policy_hash(default_policy()) == policy_hash(default_policy())


def test_all_substantive_tampers_are_detected():
    locked = policy_hash(default_policy())
    battery = run_tamper_battery(locked)
    assert len(battery) == 7
    assert all(t["detected"] for t in battery)


def test_no_equivalence_raises_false_tamper():
    locked = policy_hash(default_policy())
    battery = run_equivalence_battery(locked)
    assert len(battery) == 4
    assert all(not e["false_tamper"] for e in battery)
    # semantics-preserving re-serialization must reproduce the locked hash
    assert all(e["hash"] == locked for e in battery)


def test_is_material_under_respects_policy():
    policy = default_policy()
    # a clearly faithful (all-zero) divergence vector is not material
    faithful = {ax: 0.0 for ax in policy["axes"]}
    assert is_material_under(faithful, policy) is False


def test_meta_integrity_verdict_logic():
    assert meta_integrity_verdict(True, 1.0, 0.0) == PASS
    assert meta_integrity_verdict(True, 0.99, 0.0) == FAIL
    assert meta_integrity_verdict(True, 1.0, 0.25) == FAIL
    # non-reproducible hash is a kill-switch, not a graded fail
    assert meta_integrity_verdict(False, 1.0, 0.0) == HOLD
