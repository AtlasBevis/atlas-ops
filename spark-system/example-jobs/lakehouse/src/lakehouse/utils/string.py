"""Quote / parse multipart identifiers trả về từ Spark SQL."""

from __future__ import annotations


def quote(parts: list[str]) -> str:
    return ".".join(f"`{p}`" for p in parts)


def parse_namespace(name: str) -> list[str]:
    """Tách multipart namespace từ SHOW NAMESPACES.

    Spark quote phần có ``-`` (vd ``raw.`credit-bureau```) — bỏ backtick rồi
    mới ``split(".")``, tránh SQL kiểu `` `lakehouse`.`raw`.``credit-bureau`` ``.
    """
    clean = name.replace("`", "")
    namespaces = clean.split(".")
    return [ns for ns in namespaces if ns]
