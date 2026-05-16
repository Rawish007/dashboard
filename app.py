from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "umeedsecret"


# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # analytics table
    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )
    """)

    # users table (NEW)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # create default admin ONLY ONCE
    c.execute("SELECT * FROM users WHERE username=?", ("rawish",))
    admin = c.fetchone()

    if not admin:
        c.execute("INSERT INTO users(username, password) VALUES(?,?)",
                  ("rawish", "12345"))

    conn.commit()
    conn.close()

init_db()


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return "Invalid login"

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# =========================
# CHANGE PASSWORD
# =========================
@app.route("/change-password", methods=["POST"])
def change_password():

    if "user" not in session:
        return redirect("/login")

    old = request.form["old"]
    new = request.form["new"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (session["user"], old))

    user = c.fetchone()

    if user:
        c.execute("UPDATE users SET password=? WHERE username=?",
                  (new, session["user"]))
        conn.commit()
        conn.close()
        return "Password updated successfully"
    else:
        conn.close()
        return "Old password wrong"


# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM analytics")
    data = c.fetchall()
    conn.close()

    total = 0
    labels = []
    amounts = []

    today_total = 0
    yesterday_total = 0
    this_week = 0
    last_week = 0
    this_month = 0
    last_month = 0
    this_year = 0

    best_day = 0
    worst_day = 999999999

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    last_week_number = current_week - 1

    current_month = today.month
    last_month_number = current_month - 1

    current_year = today.year

    for row in data:

        amount = int(row[2])
        date = datetime.strptime(row[1], "%Y-%m-%d").date()

        total += amount
        labels.append(row[1])
        amounts.append(amount)

        if date == today:
            today_total += amount

        if date == yesterday:
            yesterday_total += amount

        if date.isocalendar()[1] == current_week:
            this_week += amount

        if date.isocalendar()[1] == last_week_number:
            last_week += amount

        if date.month == current_month:
            this_month += amount

        if date.month == last_month_number:
            last_month += amount

        if date.year == current_year:
            this_year += amount

        if amount > best_day:
            best_day = amount

        if amount < worst_day:
            worst_day = amount

    return render_template(
        "dashboard.html",
        total=total,
        today_total=today_total,
        yesterday_total=yesterday_total,
        this_week=this_week,
        last_week=last_week,
        this_month=this_month,
        last_month=last_month,
        this_year=this_year,
        best_day=best_day,
        worst_day=worst_day,
        labels=labels,
        amounts=amounts,
        data=data[::-1]
    )


# =========================
# ADMIN PANEL
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        day = request.form["day"]
        amount = request.form["amount"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO analytics(day, amount) VALUES(?, ?)",
                  (day, amount))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("admin.html")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
