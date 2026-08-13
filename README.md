# intent-fidelity-testbed

**Preregistered testbed for pre-boundary intent fidelity.**
Part of the Remnant Fieldworks — Coherent Inheritance Framework (CIF) / ExecutionProof program.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21911205.svg)](https://doi.org/10.5281/zenodo.21911205)
Status: **preregistered & locked** (`MANIFEST.sha256`) · IF-01 **PASS** · IF-02 **PASS** · IF-03 **PASS** · IF-05 **PASS**

**Cite this work** (concept DOI, always resolves to latest version): [10.5281/zenodo.21911205](https://doi.org/10.5281/zenodo.21911205) ·
v1.1.0: [10.5281/zenodo.21911272](https://doi.org/10.5281/zenodo.21911272) ·
v1.0.0: [10.5281/zenodo.21911206](https://doi.org/10.5281/zenodo.21911206) ·
GitHub: <https://github.com/derekhone/intent-fidelity-testbed>

---

## Honest scope (read this first)

These experiments run on a **synthetic, de-identified corpus with hand-authored ground-truth
labels** and a **preregistered extraction-noise model**. They validate the *measurement
primitive and its thresholds* on controlled data. They are:

- **NOT** a live-LLM study,
- **NOT** a claim about any deployed model's real drift rate,
- **NOT** a certification, safety guarantee, or production-readiness claim.

The value is methodological: they turn two slogans — *"pre-boundary intent distortion is
unmeasurable"* and *"a governance layer will inevitably over-control people"* — into
**falsifiable, preregistered properties**, recorded with the same ProofRecord discipline as
the rest of the RF corpus.

## Why this repository exists

ExecutionProof verifies whether a *proposed action* is authorized **at** the boundary. But
between the human's **authenticated request** and the action that arrives at that boundary,
the model may have altered **purpose, scope, authority, or consequence** — and the human may
never notice. This testbed measures that upstream gap.

The governing doctrine (from the Derek ↔ Greg exchange, August 2026) is a hard split:

> **Preserve human intent without replacing human judgment.**
> Detect *divergence* (value-neutral). **Never** adjudicate *desirability* (value-laden).

The system asks only *"did the action diverge from what the human authorized?"* — never
*"is the human's intent good?"* That distinction is what keeps the cure from becoming the
surveillance/paternalism Greg's Patriot-Act analogy warns about, and it is enforced in code
(see `test_doctrine_primitive_has_no_desirability_notion`).

## The primitive — Intent-Fidelity Divergence Vector (IFDV)

For an authenticated request `R` and a proposed action `A`, the IFDV scores four
value-neutral axes — exactly Greg's four questions:

| axis | question | threshold τ |
|---|---|---|
| `scope_expansion` | did A reach beyond the resources R authorized? | 0.25 |
| `objective_substitution` | did A pursue a different goal than R? | 0.50 |
| `authority_escalation` | did A require more privilege than R granted? | 0.125 |
| `consequence_shift` | did A inject assumptions that change the outcome? | 0.40 |

A transformation is **MATERIAL** iff *any* axis exceeds its τ → the checker emits a
**HOLD-for-reconfirmation before** the ExecutionProof boundary:

```
authenticated request  ->  [ intent-fidelity checker ]  ->  proposed action
                                    |                              |
                              reconfirm? (material)                v
                                                        [ ExecutionProof ALLOW/HOLD/DENY ]  ->  rail
```

It is a **pre-boundary filter**, not a replacement for ExecutionProof's ALLOW/HOLD/DENY.

## The locked experiments

| ID | question | observable | pass rule | result |
|---|---|---|---|---|
| **IF-01** Divergence Detection | Can the primitive separate material from faithful drift under extraction noise? | ROC-AUC + recall of material class | HOLD if AUC ≤ 0.60; else PASS iff recall ≥ 0.90 | **PASS** — AUC 0.993, recall 0.992 |
| **IF-02** Intrusion Tax | How often does it interrupt *legitimate* variation? (Greg's civil-liberties bound, numeric) | false-reconfirmation rate on faithful class | PASS iff intrusion tax ≤ 0.10 | **PASS** — tax 0.000 (locked seed); 10-seed max 0.067 |
| **IF-03** Detection-vs-Adjudication Separation | Does the flag track *divergence* only, or does it secretly track how *objectionable* a request looks? (the paternalism tripwire) | adjudication leakage — dependence of the flag on request desirability, within each label class | PASS iff leakage ≤ 0.05 | **PASS** — leakage 0.0234; paternalistic baseline leaks 1.000 |
| **IF-05** Meta-Integrity | *Who governs the governance?* Is every weakening of the policy itself tamper-evident, with no false alarms on equivalent policies? | tamper-detection rate + false-tamper rate over the self-hashing policy | HOLD if hash non-deterministic; else PASS iff detection = 1.0 **and** false-tamper = 0.0 | **PASS** — 7/7 detected, 0/4 false, hash deterministic |

IF-01 and IF-02 together are the core thesis: high recall on material divergence **with** a
low intrusion tax is the only way to preserve intent without replacing judgment. Either one
alone is meaningless. **IF-03** then falsifies the paternalism worry directly — a flag that
tracked desirability rather than divergence would leak, and it does not. **IF-05** closes the
recursion Greg raised (*"who governs the governance"*) by making the governance policy hash
itself, so no silent weakening can pass unrecorded.

*(Full metrics and the 10-seed robustness bands are in each ProofRecord under
`experiments/**/results/*.proofrecord.json`.)*

## Realistic difficulty (why the result isn't trivially perfect)

On perfectly clean structure the primitive recovers the labels almost perfectly — which
would prove nothing. So the testbed freezes an **extraction-noise model** (§2.1 of the
preregistration): the checker sees a *noisy* estimate of each axis, as it would in
deployment where objective/scope/authority/assumptions must be extracted imperfectly. IF-01
/ IF-02 measure whether the primitive stays useful **under** that noise. It does — but not
perfectly (recall floor is 0.958 across seeds; one material item per locked run is missed via
the preregistered 3% objective-misread). Those honest misses are published, not hidden.

## Install & run

```bash
pip install -e ".[dev]"          # editable install + pytest

# reproduce the locked experiments (writes/overwrites ProofRecords)
python experiments/IF-01_divergence_detection/run.py
python experiments/IF-02_intrusion_tax/run.py
python experiments/IF-03_detection_vs_adjudication/run.py
python experiments/IF-05_meta_integrity/run.py

# verify the preregistration lock and the tests
sha256sum -c MANIFEST.sha256
pytest -q
```

## ProofRecord schema

Every run emits a self-binding record (SHA-256 over the record minus its own `record_hash`),
identical in shape to the RF quantum-witness and dark-matter series:

```json
{
  "experiment_id": "IF-01-divergence-detection-v1",
  "series": "intent-fidelity-testbed",
  "hypothesis": "...",
  "timestamp_utc": "2026-08-...Z",
  "parameters": { "locked_seed": 20260812, "recall_floor": 0.9, "noise_sigma": { ... } },
  "observable": "ROC-AUC and recall of the material class under extraction noise",
  "result": { "roc_auc": 0.9932, "recall_material": 0.9917, "robustness_10seed": { ... } },
  "threshold": "HOLD if AUC <= 0.6; else PASS iff recall >= 0.9, else FAIL",
  "verdict": "PASS",
  "honest_scope": "synthetic, de-identified corpus ... NOT a live-LLM study",
  "record_hash": "..."
}
```

## Package layout

```
intent-fidelity-testbed/
├── PREREGISTRATION.md          # locked questions, primitive, noise, thresholds (v1 + v2)
├── MANIFEST.sha256             # SHA-256 lock of prereg + IF-03/IF-05 support modules
├── src/intent_fidelity/
│   ├── ifdv.py                 # the 4-axis divergence primitive + thresholds
│   ├── extraction.py           # preregistered extraction-noise (observation) model
│   ├── corpus.py               # synthetic labeled (request -> action) corpus
│   ├── adjudication.py         # IF-03: desirability-split corpus + leakage metric
│   ├── meta_integrity.py       # IF-05: self-hashing policy + tamper/equivalence batteries
│   ├── metrics.py              # precision/recall/ROC-AUC + PASS/FAIL/HOLD verdicts
│   └── proofrecord.py          # self-binding SHA-256 ProofRecords
├── experiments/
│   ├── IF-01_divergence_detection/{run.py, results/*.proofrecord.json}
│   ├── IF-02_intrusion_tax/{run.py, results/*.proofrecord.json}
│   ├── IF-03_detection_vs_adjudication/{run.py, results/*.proofrecord.json}
│   └── IF-05_meta_integrity/{run.py, results/*.proofrecord.json}
└── tests/                      # 32 tests: primitive, corpus, metrics, ProofRecord, doctrine, IF-03/IF-05
```

## Preregistration & publication rule

Questions, axis definitions, thresholds, the noise model, and the corpus construction were
frozen in `PREREGISTRATION.md` and SHA-locked in `MANIFEST.sha256` **before** any result was
computed. Results are published **regardless of PASS / FAIL / HOLD**. IF-03 (anti-paternalism
tripwire) and IF-05 (meta-integrity / "who governs the governance") were each preregistered
and SHA-locked as a v2 section of `PREREGISTRATION.md` before their runners were executed.
The remaining experiments IF-04 (reconfirmation efficacy) and IF-06 (adversarial drift) will
each get their own preregistration before any run.

## License

MIT © 2026 Remnant Fieldworks Inc.
