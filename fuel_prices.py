from __future__ import annotations

import json
import re
import sqlite3
import urllib.request
from datetime import datetime, timedelta

from database import get_connection, init_db


PRICE_SOURCE_URL = "https://petroilsa.com/precios/"
CACHE_HOURS = 6


def parse_cop_currency(value: str) -> float:
    cleaned = value.strip().replace("$", "").replace(".", "").replace(",", ".")
    return float(cleaned)


def fetch_live_prices() -> dict[str, dict[str, str | float]]:
    with urllib.request.urlopen(PRICE_SOURCE_URL, timeout=20) as response:
        html = response.read().decode("utf-8", errors="ignore")

    patterns = {
        "Corriente": r"Gasolina Corriente Petroil P87R.*?\$([\d\.,]+)",
        "Extra": r"Gasolina Extra Petroil P90 Venta Nacional.*?\$([\d\.,]+)",
    }

    prices = {}
    for fuel_type, pattern in patterns.items():
        match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
        if not match:
            raise ValueError(f"No fue posible leer el precio de {fuel_type}.")
        prices[fuel_type] = {
            "precio_galon": parse_cop_currency(match.group(1)),
            "fuente": PRICE_SOURCE_URL,
            "actualizado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    return prices


def get_cached_prices() -> dict[str, dict[str, str | float]]:
    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT tipo_combustible, precio_galon, fuente, actualizado_en
                FROM precios_combustible
                """
            ).fetchall()
    except sqlite3.OperationalError as error:
        if "no such table" not in str(error).lower():
            raise
        init_db()
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT tipo_combustible, precio_galon, fuente, actualizado_en
                FROM precios_combustible
                """
            ).fetchall()

    return {
        row["tipo_combustible"]: {
            "precio_galon": row["precio_galon"],
            "fuente": row["fuente"],
            "actualizado_en": row["actualizado_en"],
        }
        for row in rows
    }


def cache_prices(prices: dict[str, dict[str, str | float]]) -> None:
    with get_connection() as connection:
        connection.executemany(
            """
            INSERT INTO precios_combustible (
                tipo_combustible,
                precio_galon,
                fuente,
                actualizado_en
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(tipo_combustible) DO UPDATE SET
                precio_galon = excluded.precio_galon,
                fuente = excluded.fuente,
                actualizado_en = excluded.actualizado_en
            """,
            [
                (
                    fuel_type,
                    values["precio_galon"],
                    values["fuente"],
                    values["actualizado_en"],
                )
                for fuel_type, values in prices.items()
            ],
        )


def prices_are_fresh(prices: dict[str, dict[str, str | float]]) -> bool:
    if "Corriente" not in prices or "Extra" not in prices:
        return False

    try:
        updated_at = datetime.strptime(
            prices["Corriente"]["actualizado_en"], "%Y-%m-%d %H:%M:%S"
        )
    except (KeyError, ValueError, TypeError):
        return False

    return datetime.now() - updated_at < timedelta(hours=CACHE_HOURS)


def get_fuel_prices() -> dict[str, dict[str, str | float]]:
    cached = get_cached_prices()
    if prices_are_fresh(cached):
        return cached

    try:
        live_prices = fetch_live_prices()
    except Exception:
        if cached:
            return cached
        raise

    cache_prices(live_prices)
    return live_prices


def fuel_prices_as_json() -> str:
    return json.dumps(get_fuel_prices(), ensure_ascii=False)
