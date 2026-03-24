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
            """
        )
    init_db()
