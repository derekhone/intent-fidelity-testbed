"""Unit tests for the Intent-Fidelity Divergence Vector primitive."""

from intent_fidelity import (
    DEFAULT_TAU,
    Envelope,
    authority_escalation,
    authority_level,
    consequence_shift,
    ifdv,
    is_material,
    objective_substitution,
    scope_expansion,
)
from intent_fidelity.corpus import CONSEQUENCE_WEIGHTS, SYNONYMS


def test_identity_action_has_zero_divergence():
    r = Envelope("refund_customer", {"payments.refund"}, "write")
    v = ifdv(r, r)
    assert all(val == 0.0 for val in v.values())
    assert is_material(v) is False


def test_authority_ladder_is_ordinal():
    assert authority_level("read") < authority_level("write") < authority_level("root")
    assert authority_level("unknown") == 0


def test_authority_drop_is_not_divergence():
    r = Envelope("x", {"a"}, "admin")
    a = Envelope("x", {"a"}, "read")
    assert authority_escalation(r, a) == 0.0


def test_authority_escalation_positive():
    r = Envelope("x", {"a"}, "read")
    a = Envelope("x", {"a"}, "admin")
    assert authority_escalation(r, a) > DEFAULT_TAU["authority_escalation"]


def test_in_scope_child_is_downweighted_vs_out_of_scope():
    r = Envelope("x", {"db.users"}, "read")
    child = Envelope("x", {"db.users", "db.users.email"}, "read")
    stranger = Envelope("x", {"db.users", "payments.all"}, "read")
    assert scope_expansion(r, child) < scope_expansion(r, stranger)


def test_objective_synonym_is_faithful_but_swap_is_material():
    r = Envelope("refund_customer", {"a"}, "write")
    para = Envelope("issue_refund", {"a"}, "write")   # synonym -> same canonical
    swap = Envelope("close_account", {"a"}, "write")
    assert objective_substitution(r, para, SYNONYMS) == 0.0
    assert objective_substitution(r, swap, SYNONYMS) == 1.0


def test_consequence_weight_distinguishes_benign_from_heavy():
    r = Envelope("x", {"a"}, "read")
    benign = Envelope("x", {"a"}, "read", {"assume_pdf_format"})
    heavy = Envelope("x", {"a"}, "read", {"assume_irreversible_ok"})
    assert consequence_shift(r, benign, CONSEQUENCE_WEIGHTS) < DEFAULT_TAU["consequence_shift"]
    assert consequence_shift(r, heavy, CONSEQUENCE_WEIGHTS) > DEFAULT_TAU["consequence_shift"]


def test_is_material_flags_any_axis_over_threshold():
    r = Envelope("x", {"a"}, "read")
    a = Envelope("x", {"a", "unrelated.big", "another.big", "third.big"}, "read")
    v = ifdv(r, a)
    assert v["scope_expansion"] > DEFAULT_TAU["scope_expansion"]
    assert is_material(v) is True


def test_doctrine_primitive_has_no_desirability_notion():
    """Anti-paternalism guard: an unusual-but-faithful action must not flag."""
    r = Envelope("delete_records", {"db.logs.2019"}, "admin", {"assume_irreversible_ok"})
    # model faithfully reproduces the exact (aggressive) request
    v = ifdv(r, r, synonyms=SYNONYMS, consequence_weights=CONSEQUENCE_WEIGHTS)
    assert is_material(v) is False  # faithful reproduction is never material
