"""Shared helpers for tolerant CSV imports (different header names, ',' or
';' separator) used by csv_import.py and stats_import.py."""
import csv
import re


def normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.strip().lower())


def find_column(normalized_headers: dict[str, str], candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in normalized_headers:
            return normalized_headers[candidate]
    return None


def sniff_dialect(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","
