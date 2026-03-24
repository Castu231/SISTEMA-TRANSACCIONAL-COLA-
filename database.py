from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "gasolinera.db"
DEFAULT_PUMPS = 5
DEFAULT_SPEED = 0.5


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS vehiculos (
                id_vehiculo INTEGER PRIMARY KEY AUTOINCREMENT,
                placa TEXT NOT NULL UNIQUE,
                capacidad_tanque REAL NOT NULL,
                nivel_actual REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS cola (
                id_cola INTEGER PRIMARY KEY AUTOINCREMENT,
                id_vehiculo INTEGER NOT NULL,
                hora_llegada TEXT NOT NULL,
                cantidad_solicitada REAL NOT NULL,
                estado TEXT NOT NULL CHECK (estado IN ('esperando', 'en servicio', 'finalizado')),
                FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo)
            );

            CREATE TABLE IF NOT EXISTS bombas (
                id_bomba INTEGER PRIMARY KEY AUTOINCREMENT,
                estado TEXT NOT NULL CHECK (estado IN ('libre', 'ocupada')),
                velocidad_litro_segundo REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transacciones (
                id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
                id_vehiculo INTEGER NOT NULL,
                id_bomba INTEGER NOT NULL,
                litros_suministrados REAL NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                tiempo_espera INTEGER NOT NULL,
                FOREIGN KEY (id_vehiculo) REFERENCES vehiculos(id_vehiculo),
                FOREIGN KEY (id_bomba) REFERENCES bombas(id_bomba)
            );

            CREATE TABLE IF NOT EXISTS precios_combustible (
                tipo_combustible TEXT PRIMARY KEY,
                precio_galon REAL NOT NULL,
                fuente TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            );
            """
        )

        ensure_column(connection, "cola", "tipo_combustible", "TEXT DEFAULT 'Corriente'")
        ensure_column(connection, "cola", "galones_solicitados", "REAL DEFAULT 0")
        ensure_column(connection, "cola", "precio_galon", "REAL DEFAULT 0")
        ensure_column(connection, "cola", "costo_estimado", "REAL DEFAULT 0")

        ensure_column(connection, "transacciones", "combustible", "TEXT DEFAULT 'Corriente'")
        ensure_column(connection, "transacciones", "galones_suministrados", "REAL DEFAULT 0")
        ensure_column(connection, "transacciones", "precio_galon", "REAL DEFAULT 0")
        ensure_column(connection, "transacciones", "costo_total", "REAL DEFAULT 0")
        ensure_column(connection, "transacciones", "fuente_precio", "TEXT DEFAULT ''")
        ensure_column(connection, "transacciones", "fecha_precio", "TEXT DEFAULT ''")

        connection.execute(
            """
            UPDATE cola
            SET galones_solicitados = cantidad_solicitada
            WHERE galones_solicitados = 0 AND cantidad_solicitada > 0
            """
        )
        connection.execute(
            """
            UPDATE transacciones
            SET galones_suministrados = litros_suministrados / 3.78541
            WHERE galones_suministrados = 0 AND litros_suministrados > 0
            """
        )

        existing_pumps = connection.execute(
            "SELECT COUNT(*) AS total FROM bombas"
        ).fetchone()["total"]

        missing_pumps = DEFAULT_PUMPS - existing_pumps
        if missing_pumps > 0:
            connection.executemany(
                """
                INSERT INTO bombas (estado, velocidad_litro_segundo)
                VALUES (?, ?)
                """,
                [("libre", DEFAULT_SPEED) for _ in range(missing_pumps)],
            )


def reset_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            DELETE FROM transacciones;
            DELETE FROM cola;
            DELETE FROM vehiculos;
            DELETE FROM bombas;
            DELETE FROM precios_combustible;
            """
        )
    init_db()
