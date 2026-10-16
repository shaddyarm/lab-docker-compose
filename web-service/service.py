from datetime import datetime, timezone

from flask import Flask, jsonify, request


app = Flask(__name__)


def valid_integer(value, minimum, maximum):
    return type(value) is int and minimum <= value <= maximum


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/estimate")
def estimate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Ожидается JSON с данными автомобиля."}), 400

    current_year = datetime.now(timezone.utc).year
    base_price = data.get("base_price_rub")
    year = data.get("year")
    mileage = data.get("mileage_km")
    if not valid_integer(base_price, 1, 100_000_000):
        return jsonify({"error": "Некорректная базовая цена."}), 400
    if not valid_integer(year, 1980, current_year):
        return jsonify({"error": "Некорректный год выпуска."}), 400
    if not valid_integer(mileage, 0, 1_000_000):
        return jsonify({"error": "Некорректный пробег."}), 400

    age = current_year - year
    age_factor = max(0.25, 0.90 ** age)
    mileage_factor = max(0.50, 1 - mileage / 500_000)
    price = round(base_price * age_factor * mileage_factor / 1_000) * 1_000
    return jsonify({
        "estimated_price_rub": price,
        "reference_year": current_year,
        "age_years": age,
        "age_factor": round(age_factor, 4),
        "mileage_factor": round(mileage_factor, 4),
    })
