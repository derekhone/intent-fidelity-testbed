"""Detection metrics and verdict logic for the intent-fidelity-testbed series.

Provides precision / recall / ROC-AUC helpers and the PASS / FAIL / HOLD
verdict logic that maps preregistered thresholds onto measured detector
performance. Pure-Python (no sklearn dependency) so the whole testbed runs
with numpy only and every number is reproducible from the source.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

PASS = "PASS"
FAIL = "FAIL"
HOLD = "HOLD"

# Kill / HOLD threshold (PREREGISTRATION.md section 3): if the primitive cannot
# separate faithful from material transformations above this AUC, it is not a
# valid detector and no PASS/FAIL on the detection question is issued.
CHANCE_AUC = 0.60


def confusion(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, int]:
    """Return TP/FP/TN/FN counts. 1 == material, 0 == faithful."""
    tp = fp = tn = fn = 0
    for t, p in zip(y_true, y_pred):
        if t == 1 and p == 1:
            tp += 1
        elif t == 0 and p == 1:
            fp += 1
        elif t == 0 and p == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def precision(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    c = confusion(y_true, y_pred)
    denom = c["tp"] + c["fp"]
    return c["tp"] / denom if denom else 0.0


def recall(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """Recall on the material (positive) class."""
    c = confusion(y_true, y_pred)
    denom = c["tp"] + c["fn"]
    return c["tp"] / denom if denom else 0.0


def false_positive_rate(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    """FPR on the faithful (negative) class == the *intrusion tax*.

    Fraction of faithful transformations that were (wrongly) flagged material
    and would therefore have triggered a needless reconfirmation.
    """
    c = confusion(y_true, y_pred)
    denom = c["fp"] + c["tn"]
    return c["fp"] / denom if denom else 0.0


def f1(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    p, r = precision(y_true, y_pred), recall(y_true, y_pred)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def roc_points(
    y_true: Sequence[int], scores: Sequence[float]
) -> List[Tuple[float, float]]:
    """Return (FPR, TPR) points by sweeping the decision threshold over scores."""
    thresholds = sorted(set(scores), reverse=True)
    thresholds = [float("inf")] + thresholds
    pts: List[Tuple[float, float]] = []
    for thr in thresholds:
        y_pred = [1 if s >= thr and thr != float("inf") else 0 for s in scores]
        pts.append((false_positive_rate(y_true, y_pred), recall(y_true, y_pred)))
    pts.append((1.0, 1.0))
    pts = sorted(set(pts))
    return pts


def roc_auc(y_true: Sequence[int], scores: Sequence[float]) -> float:
    """Area under the ROC curve via the trapezoidal rule over swept thresholds."""
    pts = roc_points(y_true, scores)
    auc = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        auc += (x1 - x0) * (y0 + y1) / 2.0
    return auc


def detection_verdict(
    auc: float,
    recall_at_operating: float,
    recall_floor: float,
    *,
    chance_auc: float = CHANCE_AUC,
) -> str:
    """Verdict for IF-01 (divergence detection).

    HOLD if the primitive is not separable above chance (auc <= chance_auc):
    the detector is not valid, so no PASS/FAIL on the question is issued.
    Otherwise PASS iff recall at the preregistered operating threshold meets
    the floor; else FAIL.
    """
    if auc <= chance_auc:
        return HOLD
    return PASS if recall_at_operating >= recall_floor else FAIL


def intrusion_verdict(intrusion_tax: float, ceiling: float) -> str:
    """Verdict for IF-02 (intrusion tax).

    PASS iff the false-reconfirmation rate on benign variation is at or below
    the preregistered ceiling; else FAIL. A layer that interrupts legitimate
    variation IS the paternalism failure Greg warned about.
    """
    return PASS if intrusion_tax <= ceiling else FAIL


__all__ = [
    "PASS",
    "FAIL",
    "HOLD",
    "CHANCE_AUC",
    "confusion",
    "precision",
    "recall",
    "false_positive_rate",
    "f1",
    "roc_points",
    "roc_auc",
    "detection_verdict",
    "intrusion_verdict",
]
