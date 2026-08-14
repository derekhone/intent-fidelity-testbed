
---

## 7. Preregistration `v3` — IF-04 and IF-06

**Preregistration date:** 2026-08-13
**Status:** LOCKED (this file's SHA-256 recorded in `MANIFEST.sha256`)
**Covenant:** identical to section 0. Questions and thresholds below are fixed **before** any
IF-04 / IF-06 result is computed; every run emits a self-binding ProofRecord; publish
regardless of `PASS` / `FAIL` / `HOLD`.

### EXPERIMENT IF-04 — Reconfirmation Efficacy

**Question.** When the IFDV checker correctly flags a material transformation for
reconfirmation, does the divergence vector provide *actionable* information — specifically,
does its dominant axis (the axis with the highest normalized divergence `axis/τ`) correctly
identify the TYPE of divergence that occurred?

**Background.** Detection without attribution is obstruction. If the reconfirmation message
says only "something changed, approve?", the human cannot make an informed decision. Accurate
axis attribution transforms the flag from a generic interruption into an informative alert:
"authority was escalated from write to admin" vs "are you sure?". This is a necessary condition
for the checker to be useful without being paternalistic — the human gets *information*, not
just *interruption*.

**Observable.** `axis_attribution_accuracy` = fraction of true positives where the dominant
IFDV axis matches the ground-truth category of the transformation. The ground-truth
mapping (frozen):

| corpus category | expected dominant axis |
|---|---|
| `material.scope_creep` | `scope_expansion` |
| `material.scope_creep.subtle` | `scope_expansion` |
| `material.objective_swap` | `objective_substitution` |
| `material.objective_swap.subtle` | `objective_substitution` |
| `material.authority_escalation` | `authority_escalation` |
| `material.authority_escalation.subtle` | `authority_escalation` |
| `material.consequence_injection` | `consequence_shift` |
| `material.consequence_injection.subtle` | `consequence_shift` |

Secondary observables (non-verdict): false-positive axis profile (which axis drives false
alarms), 10-seed robustness band.

**Detector.** The frozen v1 IFDV primitive + v1 extraction-noise model + v1 corpus
(`n_per_cell = 30`, locked seed `20260812`).

**Preregistered threshold.**
- **HOLD** (kill) iff recall < 0.60 (not enough true positives to measure attribution).
- Otherwise **PASS** iff `axis_attribution_accuracy >= 0.80`; else **FAIL**.

### EXPERIMENT IF-06 — Adversarial Drift

**Question.** Can a deliberate adversary construct material transformations that evade the
IFDV checker by distributing divergence across multiple axes, each kept just below its
individual threshold `τ`?

**Background.** The IFDV checker uses per-axis thresholds with OR logic: any single axis
exceeding its `τ` triggers the flag. A strategic adversary who knows the thresholds might
try to spread material change across all four axes without crossing any single one. IF-06
tests this specific evasion strategy.

**Adversarial corpus construction (frozen).** `n = 120` items at locked seed `20260812`:
- Each item starts from one of 5 base request envelopes.
- Scope: randomly add 1–2 tokens (60% close/child tokens, 40% far/out-of-scope).
- Authority: 30% of items attempt a 1-step escalation; 70% hold authority constant.
- Consequence: inject 1–3 benign assumptions (weights 0.05–0.10).
- Objective: always kept identical (no substitution).

The items are genuinely material (multi-axis change occurred) but designed to stay near or
below individual axis thresholds. This is NOT an adaptive adversary; it models the
*fixed-strategy* evasion that a known-threshold system is most vulnerable to.

**Observable.** `evasion_rate` = fraction of adversarial items that evade detection (are NOT
flagged as material). Secondary: adversarial `divergence_score` distribution, comparison
with regular corpus evasion rate, 10-seed robustness band.

**Preregistered threshold.**
- **PASS** iff `evasion_rate <= 0.15`; else **FAIL**. The checker must catch at least 85%
  of adversarial attempts; a higher evasion rate indicates the per-axis OR logic is
  insufficient and a composite threshold is needed.

### 7.1 v3 freeze

Upon writing this file's SHA-256 to `MANIFEST.sha256`, sections 1–6 of v1/v2 plus the IF-04
and IF-06 experiments above are frozen for version `v3` of the `intent-fidelity-testbed`
series.
