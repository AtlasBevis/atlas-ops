"""Enumerate every namespace in the catalog, recursing into nested namespaces."""

from __future__ import annotations

from collections.abc import Iterator

from pyspark.sql import SparkSession

from lakehouse.utils.string import parse_namespace, quote


def list_namespaces(
    spark: SparkSession, catalog: str, parent: list[str] | None = None
) -> Iterator[list[str]]:
    parent = parent or []
    target = quote([catalog, *parent])

    for row in spark.sql(f"SHOW NAMESPACES IN {target}").collect():
        parts = parse_namespace(row[0])

        if parent and parts[: len(parent)] != parent:
            parts = [*parent, *parts]

        if not parts:
            continue
        yield parts
        yield from list_namespaces(spark, catalog, parts)
