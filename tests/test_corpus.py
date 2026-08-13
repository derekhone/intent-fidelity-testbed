"""Tests for the synthetic corpus and its ground-truth labels."""

from intent_fidelity import build_corpus, divergence_score, ifdv, is_material
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS
from intent_fidelity.extraction import observe


def test_corpus_is_deterministic_for_seed():
    a = build_corpus(seed=123)
    b = build_corpus(seed=123)
    assert [x.item_id for x in a] == [y.item_id for y in b]
    assert [x.category for x in a] == [y.category for y in b]


def test_corpus_is_balanced_and_labeled():
    c = build_corpus(n_per_cell=30)
    assert len(c) == 210  # 3 faithful cells + 4 material cells, 30 each
    assert sum(1 for x in c if x.label == 0) == 90
    assert sum(1 for x in c if x.label == 1) == 120
    assert all(x.label in (0, 1) for x in c)


def test_faithful_labels_match_faithful_categories():
    c = build_corpus()
    for x in c:
        if x.category.startswith("faithful."):
            assert x.label == 0
        if x.category.startswith("material."):
            assert x.label == 1


def test_clean_primitive_recovers_labels_well_without_noise():
    """On clean structure the primitive should be near-perfect (sanity)."""
    c = build_corpus()
    correct = 0
    for it in c:
        v = ifdv(it.request, it.action, synonyms=SYNONYMS,
                 consequence_weights=CONSEQUENCE_WEIGHTS)
        pred = 1 if is_material(v) else 0
        correct += (pred == it.label)
    assert correct / len(c) >= 0.98


def test_extraction_noise_is_reproducible():
    c = build_corpus(seed=7)
    it = c[0]
    clean = ifdv(it.request, it.action, synonyms=SYNONYMS,
                 consequence_weights=CONSEQUENCE_WEIGHTS)
    o1 = observe(clean, it.item_id, 7)
    o2 = observe(clean, it.item_id, 7)
    assert o1 == o2  # deterministic given (seed, item_id)


def test_divergence_score_over_one_iff_material():
    r_over = {"scope_expansion": 0.9, "objective_substitution": 0.0,
              "authority_escalation": 0.0, "consequence_shift": 0.0}
    r_under = {"scope_expansion": 0.1, "objective_substitution": 0.0,
               "authority_escalation": 0.0, "consequence_shift": 0.0}
    assert divergence_score(r_over) > 1.0
    assert divergence_score(r_under) < 1.0
