#!/usr/bin/env python3
"""Avro Names: sanitize topic segments into legal name / namespace."""

from __future__ import annotations

import re

# https://avro.apache.org/docs/++version++/specification/#names
AVRO_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
AVRO_NAMESPACE_RE = re.compile(
    r"^([A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*)?$"
)
_AVRO_ILLEGAL_IN_NAME = re.compile(r"[^A-Za-z0-9_]+")


def avro_name_segment(part: str) -> str:
    """Sanitize one dot-separated segment to a legal Avro name.

    Spec: start with ``[A-Za-z_]``, then only ``[A-Za-z0-9_]``.
    Illegal runs (``-``, ``$``, space, …) become ``_``; leading digit → prefix ``_``.
    """
    cleaned = _AVRO_ILLEGAL_IN_NAME.sub("_", part)
    if not cleaned:
        cleaned = "_"
    if cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    if not AVRO_NAME_RE.fullmatch(cleaned):
        raise ValueError(f"Cannot form Avro name from segment {part!r} → {cleaned!r}")
    return cleaned


def avro_namespace(topic: str) -> str:
    """Derive a legal Avro namespace from a Kafka topic / topicPrefix path.

    Kafka topics may contain ``-`` (e.g. ``card-bo``); those characters are
    illegal in Avro and are replaced via :func:`avro_name_segment`.
    """
    text = topic.strip().strip(".")
    if not text:
        return ""
    segments = [avro_name_segment(p) for p in text.split(".") if p != ""]
    ns = ".".join(segments)
    if not AVRO_NAMESPACE_RE.fullmatch(ns):
        raise ValueError(
            f"Invalid Avro namespace derived from topic {topic!r}: {ns!r}"
        )
    return ns
