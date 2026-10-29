"""SparkSession wired to a Lakekeeper (Iceberg REST) catalog."""

from __future__ import annotations

from pyspark.sql import SparkSession

from lakehouse.configs.catalog import CatalogConfig


def get_or_create_session(
    catalog: CatalogConfig, app_name: str = "lakehouse"
) -> SparkSession:
    prefix = f"spark.sql.catalog.{catalog.name}"
    builder = (
        SparkSession.builder.appName(app_name)
        .config(
            "spark.sql.extensions",
            "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
        )
        .config(prefix, "org.apache.iceberg.spark.SparkCatalog")
        .config(f"{prefix}.type", "rest")
        .config(f"{prefix}.uri", catalog.uri)
        .config(f"{prefix}.warehouse", catalog.warehouse)
        .config(f"{prefix}.header.X-Iceberg-Access-Delegation", "vended-credentials")
        .config("spark.sql.defaultCatalog", catalog.name)
    )

    if catalog.credential:
        builder = builder.config(f"{prefix}.credential", catalog.credential)
        builder = builder.config(f"{prefix}.rest.auth.type", "oauth2")
        if catalog.oauth2_server_uri:
            builder = builder.config(
                f"{prefix}.oauth2-server-uri", catalog.oauth2_server_uri
            )
        if catalog.scope:
            builder = builder.config(f"{prefix}.scope", catalog.scope)

    for key, value in catalog.extra_spark_conf.items():
        builder = builder.config(key, str(value))

    spark = builder.getOrCreate()
    # Tắt INFO của Spark/Iceberg (MemoryStore, broadcast, CodeGenerator...) để log
    # của job (logger ``lakehouse.*``, Python logging) không bị chìm.
    spark.sparkContext.setLogLevel("WARN")
    return spark
