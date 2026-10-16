import json
import os
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request


app = Flask(__name__)
SERVICE_URL = os.environ.get("VALUATION_SERVICE_URL", "http://web-service:8001")


def db_connection():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "car_value"),
        user=os.environ.get("DB_USER", "car_user"),
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )


def valid_integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


@app.get("/api/health")
def health():
    with db_connection() as connection:
        connection.execute("SELECT 1")
    with urlopen(f"{SERVICE_URL}/health", timeout=2) as response:
        if response.status != 200:
            return jsonify({"status": "error"}), 503
    return jsonify({"status": "ok"})


@app.get("/api/models")
def models():
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT id, name, base_price_rub FROM car_models ORDER BY id"
        ).fetchall()
    return jsonify(rows)


@app.get("/api/valuations")
def valuations():
    with db_connection() as connection:
        rows = connection.execute(
            "SELECT h.id, m.name AS model_name, h.year, h.mileage_km, "
            "h.estimated_price_rub, h.created_at "
            "FROM valuation_history h JOIN car_models m ON m.id = h.model_id "
            "ORDER BY h.id DESC LIMIT 50"
        ).fetchall()
    for row in rows:
        row["created_at"] = row["created_at"].isoformat()
    return jsonify(rows)


@app.post("/api/valuations")
def create_valuation():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Отправьте JSON с данными автомобиля."}), 400

    model_id = data.get("model_id")
    year = data.get("year")
    mileage = data.get("mileage_km")
    if not valid_integer(model_id, 1, 1_000_000):
        return jsonify({"error": "Выберите модель автомобиля."}), 400
    if not valid_integer(year, 1980, datetime.now(timezone.utc).year):
        return jsonify({"error": "Некорректный год выпуска."}), 400
    if not valid_integer(mileage, 0, 1_000_000):
        return jsonify({"error": "Пробег должен быть от 0 до 1 000 000 км."}), 400

    with db_connection() as connection:
        model = connection.execute(
            "SELECT id, name, base_price_rub FROM car_models WHERE id = %s",
            (model_id,),
        ).fetchone()
    if model is None:
        return jsonify({"error": "Модель не найдена."}), 404

    payload = json.dumps({
        "base_price_rub": model["base_price_rub"],
        "year": year,
        "mileage_km": mileage,
    }).encode("utf-8")
    service_request = Request(
        f"{SERVICE_URL}/estimate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(service_request, timeout=5) as response:
            estimate = json.load(response)
    except (URLError, TimeoutError, ValueError) as error:
        app.logger.warning("Valuation service failed: %s", error)
        return jsonify({"error": "Сервис оценки временно недоступен."}), 502

    price = estimate.get("estimated_price_rub")
    if not valid_integer(price, 0, 100_000_000):
        return jsonify({"error": "Сервис вернул некорректную стоимость."}), 502

    with db_connection() as connection:
        row = connection.execute(
            "INSERT INTO valuation_history (model_id, year, mileage_km, estimated_price_rub) "
            "VALUES (%s, %s, %s, %s) "
            "RETURNING id, year, mileage_km, estimated_price_rub, created_at",
            (model_id, year, mileage, price),
        ).fetchone()
    row["model_name"] = model["name"]
    row["created_at"] = row["created_at"].isoformat()
    return jsonify(row), 201
