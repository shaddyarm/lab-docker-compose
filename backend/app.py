import os

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request


app = Flask(__name__)


def db_connection():
    return psycopg.connect(
        host=os.environ.get("DB_HOST", "db"),
        dbname=os.environ.get("DB_NAME", "library"),
        user=os.environ.get("DB_USER", "library_user"),
        password=os.environ["DB_PASSWORD"],
        row_factory=dict_row,
    )


@app.get("/api/health")
def health():
    with db_connection() as connection:
        connection.execute("SELECT 1")
    return jsonify({"status": "ok"})


@app.get("/api/books")
def list_books():
    status = request.args.get("status", "all")
    if status not in ("all", "read"):
        return jsonify({"error": "Неизвестный фильтр книг."}), 400

    query = "SELECT id, title, author, is_read FROM books"
    if status == "read":
        query += " WHERE is_read = true"
    query += " ORDER BY id"

    with db_connection() as connection:
        books = connection.execute(query).fetchall()
    return jsonify(books)


@app.get("/api/stats")
def stats():
    with db_connection() as connection:
        counts = connection.execute(
            "SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE is_read) AS read FROM books"
        ).fetchone()
    return jsonify(counts)


@app.post("/api/books")
def add_book():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Отправьте JSON с данными книги."}), 400

    title = data.get("title")
    author = data.get("author")
    is_read = data.get("is_read", False)
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 150:
        return jsonify({"error": "Название должно содержать от 1 до 150 символов."}), 400
    if not isinstance(author, str) or not 1 <= len(author.strip()) <= 120:
        return jsonify({"error": "Автор должен содержать от 1 до 120 символов."}), 400
    if not isinstance(is_read, bool):
        return jsonify({"error": "Поле is_read должно быть логическим значением."}), 400

    with db_connection() as connection:
        book = connection.execute(
            "INSERT INTO books (title, author, is_read) VALUES (%s, %s, %s) "
            "RETURNING id, title, author, is_read",
            (title.strip(), author.strip(), is_read),
        ).fetchone()
    return jsonify(book), 201
