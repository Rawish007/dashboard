from flask import Flask, render_template, request, redirect, jsonify
import sqlite3

app = Flask(__name__)

# ---------------- DB ----------------
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS thoughts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        mood TEXT NOT NULL,
        country TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ----------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/post", methods=["POST"])
def post_thought():
    text = request.form["text"]
    mood = request.form["mood"]
    country = request.form.get("country", "Unknown")

    conn = get_db()
    conn.execute("INSERT INTO thoughts (text, mood, country) VALUES (?, ?, ?)",
                 (text, mood, country))
    conn.commit()
    conn.close()

    return redirect("/")

@app.route("/api/thoughts")
def get_thoughts():
    conn = get_db()
    thoughts = conn.execute("SELECT * FROM thoughts ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()

    return jsonify([dict(row) for row in thoughts])

if __name__ == "__main__":
    app.run(debug=True)
