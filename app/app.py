from flask import Flask, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "taskdb"),
        user=os.getenv("DB_USER", "taskuser"),
        password=os.getenv("DB_PASSWORD", "taskpass"),
        port=os.getenv("DB_PORT", "5432")
    )


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            completed BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM tasks ORDER BY id")
    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(tasks)


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "INSERT INTO tasks (title) VALUES (%s) RETURNING *",
        (data["title"],)
    )

    task = cursor.fetchone()

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )

    conn.commit()

    deleted = cursor.rowcount

    cursor.close()
    conn.close()

    if deleted == 0:
        return jsonify({"error": "task not found"}), 404

    return jsonify({"message": "task deleted"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)