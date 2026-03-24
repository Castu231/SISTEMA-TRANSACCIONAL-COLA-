from __future__ import annotations

import os
from datetime import datetime, timedelta

from flask import Flask, redirect, render_template, request, url_for

from database import get_connection, init_db, reset_db


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

app = Flask(__name__)
init_db()


def now_local() -> datetime:
    return datetime.now()


def parse_dt(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


def format_dt(value: datetime) -> str:
    return value.strftime(DATE_FORMAT)


def seconds_to_label(seconds: int) -> str:
    minutes, remaining_seconds = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def sync_system_state() -> None:
    current_time = now_local()

    with get_connection() as connection:
        active_transactions = connection.execute(
            """
            SELECT t.id_transaccion, t.id_vehiculo, t.id_bomba, t.hora_fin
            FROM transacciones t
            INNER JOIN cola c ON c.id_vehiculo = t.id_vehiculo
            WHERE c.estado = 'en servicio'
            """
        ).fetchall()

        for transaction in active_transactions:
            end_time = parse_dt(transaction["hora_fin"])
            if end_time <= current_time:
                supplied_liters = connection.execute(
                    """
                    SELECT litros_suministrados
                    FROM transacciones
                    WHERE id_transaccion = ?
                    """,
                    (transaction["id_transaccion"],),
                ).fetchone()["litros_suministrados"]
                connection.execute(
                    """
                    UPDATE cola
                    SET estado = 'finalizado'
                    WHERE id_vehiculo = ? AND estado = 'en servicio'
                    """,
                    (transaction["id_vehiculo"],),
                )
                connection.execute(
                    """
                    UPDATE vehiculos
                    SET nivel_actual = MIN(capacidad_tanque, nivel_actual + ?)
                    WHERE id_vehiculo = ?
                    """,
                    (supplied_liters, transaction["id_vehiculo"]),
                )
                connection.execute(
                    """
                    UPDATE bombas
                    SET estado = 'libre'
                    WHERE id_bomba = ?
                    """,
                    (transaction["id_bomba"],),
                )

        waiting_queue = connection.execute(
            """
            SELECT c.id_cola, c.id_vehiculo, c.hora_llegada, c.cantidad_solicitada
            FROM cola c
            WHERE c.estado = 'esperando'
            ORDER BY c.hora_llegada ASC, c.id_cola ASC
            """
        ).fetchall()

        available_pumps = connection.execute(
            """
            SELECT id_bomba, velocidad_litro_segundo
            FROM bombas
            WHERE estado = 'libre'
            ORDER BY id_bomba ASC
            """
        ).fetchall()

        for queue_item, pump in zip(waiting_queue, available_pumps):
            start_time = now_local()
            arrival_time = parse_dt(queue_item["hora_llegada"])
            wait_seconds = int((start_time - arrival_time).total_seconds())
            service_seconds = max(
                1,
                int(
                round(queue_item["cantidad_solicitada"] / pump["velocidad_litro_segundo"])
                ),
            )
            end_time = start_time + timedelta(seconds=service_seconds)

            connection.execute(
                """
                INSERT INTO transacciones (
                    id_vehiculo,
                    id_bomba,
                    litros_suministrados,
                    hora_inicio,
                    hora_fin,
                    tiempo_espera
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    queue_item["id_vehiculo"],
                    pump["id_bomba"],
                    queue_item["cantidad_solicitada"],
                    format_dt(start_time),
                    format_dt(end_time),
                    max(0, wait_seconds),
                ),
            )
            connection.execute(
                """
                UPDATE cola
                SET estado = 'en servicio'
                WHERE id_cola = ?
                """,
                (queue_item["id_cola"],),
            )
            connection.execute(
                """
                UPDATE bombas
                SET estado = 'ocupada'
                WHERE id_bomba = ?
                """,
                (pump["id_bomba"],),
            )


def build_dashboard_context() -> dict:
    sync_system_state()
    current_time = now_local()

    with get_connection() as connection:
        summary = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM cola WHERE estado = 'esperando') AS esperando,
                (SELECT COUNT(*) FROM cola WHERE estado = 'en servicio') AS en_servicio,
                (SELECT COUNT(*) FROM cola WHERE estado = 'finalizado') AS finalizado,
                (SELECT COUNT(*) FROM bombas WHERE estado = 'libre') AS bombas_libres
            """
        ).fetchone()

        queue = connection.execute(
            """
            SELECT
                c.id_cola,
                v.placa,
                c.hora_llegada,
                c.cantidad_solicitada,
                c.estado
            FROM cola c
            INNER JOIN vehiculos v ON v.id_vehiculo = c.id_vehiculo
            ORDER BY
                CASE c.estado
                    WHEN 'en servicio' THEN 1
                    WHEN 'esperando' THEN 2
                    ELSE 3
                END,
                c.hora_llegada ASC
            """
        ).fetchall()

        pumps = connection.execute(
            """
            SELECT
                b.id_bomba,
                b.estado,
                b.velocidad_litro_segundo,
                v.placa,
                t.hora_inicio,
                t.hora_fin
            FROM bombas b
            LEFT JOIN transacciones t
                ON t.id_bomba = b.id_bomba
                AND t.id_transaccion = (
                    SELECT id_transaccion
                    FROM transacciones
                    WHERE id_bomba = b.id_bomba
                    ORDER BY id_transaccion DESC
                    LIMIT 1
                )
            LEFT JOIN vehiculos v ON v.id_vehiculo = t.id_vehiculo
            ORDER BY b.id_bomba ASC
            """
        ).fetchall()

        transactions = connection.execute(
            """
            SELECT
                t.id_transaccion,
                v.placa,
                t.id_bomba,
                t.litros_suministrados,
                t.hora_inicio,
                t.hora_fin,
                t.tiempo_espera
            FROM transacciones t
            INNER JOIN vehiculos v ON v.id_vehiculo = t.id_vehiculo
            ORDER BY t.id_transaccion DESC
            """
        ).fetchall()

    queue_rows = []
    for item in queue:
        arrival = parse_dt(item["hora_llegada"])
        elapsed = int((current_time - arrival).total_seconds())
        queue_rows.append(
            {
                **dict(item),
                "espera_actual": seconds_to_label(elapsed),
            }
        )

    pump_rows = []
    for pump in pumps:
        remaining = "-"
        if pump["estado"] == "ocupada" and pump["hora_fin"]:
            finish = parse_dt(pump["hora_fin"])
            remaining_seconds = int((finish - current_time).total_seconds())
            remaining = seconds_to_label(remaining_seconds)
        pump_rows.append(
            {
                **dict(pump),
                "tiempo_restante": remaining,
                "segundos_por_litro": round(1 / pump["velocidad_litro_segundo"], 2),
            }
        )

    transaction_rows = []
    for item in transactions:
        start = parse_dt(item["hora_inicio"])
        end = parse_dt(item["hora_fin"])
        duration = int((end - start).total_seconds())
        transaction_rows.append(
            {
                **dict(item),
                "tiempo_servicio": seconds_to_label(duration),
                "tiempo_espera_label": seconds_to_label(item["tiempo_espera"]),
            }
        )

    return {
        "summary": dict(summary),
        "queue": queue_rows,
        "pumps": pump_rows,
        "transactions": transaction_rows,
        "current_time": format_dt(current_time),
    }


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", **build_dashboard_context())


@app.route("/vehiculos", methods=["POST"])
def register_vehicle():
    plate = request.form["placa"].strip().upper()
    capacity = float(request.form["capacidad_tanque"])
    current_level = float(request.form["nivel_actual"])
    requested_amount = float(request.form["cantidad_a_llenar"])

    available_space = capacity - current_level
    if current_level > capacity or requested_amount <= 0 or requested_amount > available_space:
        return redirect(url_for("index"))

    with get_connection() as connection:
        vehicle = connection.execute(
            """
            SELECT id_vehiculo
            FROM vehiculos
            WHERE placa = ?
            """,
            (plate,),
        ).fetchone()

        if vehicle is None:
            cursor = connection.execute(
                """
                INSERT INTO vehiculos (placa, capacidad_tanque, nivel_actual)
                VALUES (?, ?, ?)
                """,
                (plate, capacity, current_level),
            )
            vehicle_id = cursor.lastrowid
        else:
            vehicle_id = vehicle["id_vehiculo"]
            connection.execute(
                """
                UPDATE vehiculos
                SET capacidad_tanque = ?, nivel_actual = ?
                WHERE id_vehiculo = ?
                """,
                (capacity, current_level, vehicle_id),
            )

        connection.execute(
            """
            INSERT INTO cola (id_vehiculo, hora_llegada, cantidad_solicitada, estado)
            VALUES (?, ?, ?, 'esperando')
            """,
            (vehicle_id, format_dt(now_local()), requested_amount),
        )

    sync_system_state()
    return redirect(url_for("index"))


@app.route("/reiniciar", methods=["POST"])
def restart():
    reset_db()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
