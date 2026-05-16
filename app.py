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

    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            ("rawishtahir", "RAWiSH786rawi@")
        )

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

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = username
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid Login")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# DASHBOARD
# =========================
@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    total = today_total = yesterday_total = 0
    this_week = last_week = 0
    this_month = last_month = 0
    best_day = 0

    labels = []
    amounts = []

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month

    prev_month = 12 if current_month == 1 else current_month - 1
    prev_month_year = current_year - 1 if current_month == 1 else current_year

    for row in data:
        try:
            amount = int(row[2])
            date = datetime.strptime(row[1], "%Y-%m-%d").date()

            total += amount
            labels.append(row[1])
            amounts.append(amount)

            if amount > best_day:
                best_day = amount

            if date == today:
                today_total += amount

            if date == yesterday:
                yesterday_total += amount

            if date.isocalendar()[1] == current_week and date.year == current_year:
                this_week += amount

            if date.isocalendar()[1] == current_week - 1:
                last_week += amount

            if date.month == current_month:
                this_month += amount

            if date.month == prev_month and date.year == prev_month_year:
                last_month += amount

        except:
            pass

    return render_template(
        "dashboard.html",
        total=total,
        today_total=today_total,
        yesterday_total=yesterday_total,
        this_week=this_week,
        last_week=last_week,
        this_month=this_month,
        last_month=last_month,
        best_day=best_day,
        labels=labels,
        amounts=amounts,
        data=data
    )


# =========================
# ANALYTICS (FIXED - SINGLE ROUTE ONLY)
# =========================
@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    today_val = yesterday_val = total_val = 0
    week_now = week_last = 0
    month_now = month_last = 0
    year_now = year_last = 0

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month

    for row in data:
        try:
            amount = int(row[2])
            date = datetime.strptime(row[1], "%Y-%m-%d").date()

            total_val += amount

            if date == today:
                today_val += amount

            if date == yesterday:
                yesterday_val += amount

            if date.isocalendar()[1] == current_week:
                week_now += amount

            if date.isocalendar()[1] == current_week - 1:
                week_last += amount

            if date.month == current_month:
                month_now += amount

            if date.month == current_month - 1:
                month_last += amount

            if date.year == current_year:
                year_now += amount

            if date.year == current_year - 1:
                year_last += amount

        except:
            pass

    labels = [r[1] for r in data[:10]]
    values = [r[2] for r in data[:10]]

    return render_template(
        "analytics.html",
        today_val=today_val,
        yesterday_val=yesterday_val,
        total_val=total_val,
        week_now=week_now,
        week_last=week_last,
        month_now=month_now,
        month_last=month_last,
        year_now=year_now,
        year_last=year_last,
        daily_labels=labels,
        daily_values=values,
        week_labels=labels,
        week_values=values,
        month_labels=labels,
        month_values=values,
        year_labels=labels,
        year_values=values
    )


# =========================
# ADMIN
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST":
        c.execute(
            "INSERT INTO analytics(day,amount) VALUES(?,?)",
            (request.form["day"], request.form["amount"])
        )
        conn.commit()

    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html", data=data, users=users)


# =========================
# ADD USER
# =========================
@app.route("/add-user", methods=["POST"])
def add_user():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        (request.form["username"], request.form["password"])
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE RECOVERY
# =========================
@app.route("/delete-recovery/<int:id>")
def delete_recovery(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM analytics WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE USER (PROTECTED ADMIN)
# =========================
@app.route("/delete-user/<int:id>")
def delete_user(id):
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE id=?", (id,))
    user = c.fetchone()

    if user and user[0] == "rawishtahir":
        conn.close()
        return "<h2 style='color:red'>Admin Protected</h2>"

    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
