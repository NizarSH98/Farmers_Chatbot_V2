"""Deterministic graph-relation question hints for evaluation cases."""

from __future__ import annotations


def relation_hint(
    language: str,
    predicate: str,
    subject_en: str,
    subject_ar: str,
    object_en: str,
    object_ar: str,
) -> str:
    relation = predicate.replace("_", " ")
    if language == "en":
        return f" Explain how {subject_en} {relation} {object_en}."
    if language == "arabizi":
        return f" fasser l 3ale2a {subject_en} / {relation} / {object_en}."
    if language == "code":
        return f" اربط {subject_ar or subject_en} with {object_ar or object_en} through {relation}."
    return f" اربط {subject_ar or subject_en} مع {object_ar or object_en} ووضّح علاقة {relation}."
