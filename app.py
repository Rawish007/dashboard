from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# DATABASE CREATE
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# DASHBOARD
@app.route("/")
def dashboard():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM analytics")
    data = c.fetchall()

    total = sum([row[2] for row in data])

    labels = [row[1] for row in data]
    amounts = [row[2] for row in data]

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        labels=labels,
        amounts=amounts
    )

# ADMIN PANEL
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        day = request.form["day"]
        amount = request.form["amount"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO analytics (day, amount) VALUES (?, ?)",
            (day, amount)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)
