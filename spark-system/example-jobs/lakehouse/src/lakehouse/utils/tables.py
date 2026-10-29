"""Enumerate every table in the catalog."""

from __future__ import annotations

from collections.abc import Iterator

from pyspark.sql import SparkSession

from lakehouse.utils.namespaces import list_namespaces
from lakehouse.utils.string import quote


def list_tables(spark: SparkSession, catalog: str) -> Iterator[str]:
    """Yield table identifiers as 'namespace.table' (without catalog prefix)."""
    for ns in list_namespaces(spark, catalog):
        for row in spark.sql(f"SHOW TABLES IN {quote([catalog, *ns])}").collect():
            if row["isTemporary"]:
                continue
            yield f"{'.'.join(ns)}.{row['tableName']}"
