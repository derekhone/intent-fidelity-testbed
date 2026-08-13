"""Tests for detection metrics, verdict logic, and ProofRecord discipline."""

from intent_fidelity import (
    FAIL,
    HOLD,
    PASS,
    compute_record_hash,
    detection_verdict,
    false_positive_rate,
    intrusion_verdict,
    make_proofrecord,
    precision,
    recall,
    roc_auc,
    verify_record,
)


# ---- metrics ----
def test_perfect_separation_auc_one():
    y = [0, 0, 1, 1]
    s = [0.0, 0.1, 0.9, 1.0]
    assert roc_auc(y, s) == 1.0


def test_recall_and_precision_and_fpr():
    y_true = [1, 1, 0, 0]
    y_pred = [1, 0, 1, 0]
    assert recall(y_true, y_pred) == 0.5
    assert precision(y_true, y_pred) == 0.5
    assert false_positive_rate(y_true, y_pred) == 0.5


def test_detection_verdict_hold_below_chance():
    assert detection_verdict(0.55, 1.0, 0.90) == HOLD


def test_detection_verdict_pass_and_fail():
    assert detection_verdict(0.95, 0.95, 0.90) == PASS
    assert detection_verdict(0.95, 0.80, 0.90) == FAIL


def test_intrusion_verdict():
    assert intrusion_verdict(0.05, 0.10) == PASS
    assert intrusion_verdict(0.20, 0.10) == FAIL


# ---- ProofRecord ----
def _rec():
    return make_proofrecord(
        experiment_id="TEST-1",
        hypothesis="h",
        parameters={"a": 1},
        observable="o",
        result={"x": 0.5},
        threshold="t",
        verdict=PASS,
    )


def test_record_has_required_fields_and_verifies():
    r = _rec()
    for f in ("experiment_id", "series", "hypothesis", "timestamp_utc",
              "parameters", "observable", "result", "threshold", "verdict",
              "honest_scope", "record_hash"):
        assert f in r
    assert verify_record(r) is True


def test_hash_excludes_record_hash_field():
    r = _rec()
    without = {k: v for k, v in r.items() if k != "record_hash"}
    assert r["record_hash"] == compute_record_hash(without)


def test_tampering_is_detected():
    r = _rec()
    r["result"]["x"] = 0.9  # mutate without recomputing
    assert verify_record(r) is False
