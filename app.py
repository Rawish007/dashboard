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
    CREATE TABLE IF NOT EXISTS distribution(
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

    # default admin
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
        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (request.form["username"], request.form["password"])
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
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

    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    distributions = c.fetchall()

    conn.close()

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month

    prev_month = 12 if current_month == 1 else current_month - 1
    prev_month_year = current_year - 1 if current_month == 1 else current_year

    total = today_total = yesterday_total = 0
    this_week = last_week = 0
    this_month = last_month = 0
    best_day = 0

    labels = []
    amounts = []

    for row in data:
        try:
            amount = int(row[2])
            date = datetime.strptime(row[1], "%Y-%m-%d").date()

            total += amount
            labels.append(row[1])
            amounts.append(amount)

            best_day = max(best_day, amount)

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

    distribution_total = distribution_today = distribution_yesterday = 0
    distribution_this_week = distribution_last_week = 0
    distribution_this_month = distribution_last_month = 0
    best_distribution = 0

    dist_labels = []
    dist_amounts = []

    for d in distributions:
        try:
            amount = int(d[2])
            date = datetime.strptime(d[1], "%Y-%m-%d").date()

            distribution_total += amount
            best_distribution = max(best_distribution, amount)

            dist_labels.append(d[1])
            dist_amounts.append(amount)

            if date == today:
                distribution_today += amount
            if date == yesterday:
                distribution_yesterday += amount

            if date.isocalendar()[1] == current_week and date.year == current_year:
                distribution_this_week += amount

            if date.isocalendar()[1] == current_week - 1:
                distribution_last_week += amount

            if date.month == current_month:
                distribution_this_month += amount

            if date.month == prev_month and date.year == prev_month_year:
                distribution_last_month += amount

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

        distribution_total=distribution_total,
        distribution_today=distribution_today,
        distribution_yesterday=distribution_yesterday,
        distribution_this_week=distribution_this_week,
        distribution_last_week=distribution_last_week,
        distribution_this_month=distribution_this_month,
        distribution_last_month=distribution_last_month,
        best_distribution=best_distribution,

        labels=labels,
        amounts=amounts,

        dist_labels=dist_labels,
        dist_amounts=dist_amounts,

        data=data,
        distributions=distributions
    )


# =========================
# ANALYTICS
# =========================
@app.route("/analytics")
def analytics():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    dist = c.fetchall()

    conn.close()

    today = datetime.now().date()
    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month

    # =========================
    # RECOVERY DATA
    # =========================
    labels = []
    amounts = []

    week_now = week_last = 0
    month_now = month_last = 0
    year_now = year_last = 0

    for row in data:
        try:
            amount = int(row[2])
            date = datetime.strptime(row[1], "%Y-%m-%d").date()

            labels.append(row[1])
            amounts.append(amount)

            # WEEK
            if date.isocalendar()[1] == current_week:
                week_now += amount
            if date.isocalendar()[1] == current_week - 1:
                week_last += amount

            # MONTH
            if date.month == current_month:
                month_now += amount
            if date.month == current_month - 1:
                month_last += amount

            # YEAR
            if date.year == current_year:
                year_now += amount
            if date.year == current_year - 1:
                year_last += amount

        except:
            pass

    # =========================
    # DISTRIBUTION DATA
    # =========================
    dist_labels = []
    dist_amounts = []

    distribution_this_week = 0
    distribution_last_week = 0
    distribution_this_month = 0
    distribution_last_month = 0
    distribution_this_year = 0
    distribution_last_year = 0

    for d in dist:
        try:
            amount = int(d[2])
            date = datetime.strptime(d[1], "%Y-%m-%d").date()

            dist_labels.append(d[1])
            dist_amounts.append(amount)

            # WEEK
            if date.isocalendar()[1] == current_week:
                distribution_this_week += amount
            if date.isocalendar()[1] == current_week - 1:
                distribution_last_week += amount

            # MONTH
            if date.month == current_month:
                distribution_this_month += amount
            if date.month == current_month - 1:
                distribution_last_month += amount

            # YEAR
            if date.year == current_year:
                distribution_this_year += amount
            if date.year == current_year - 1:
                distribution_last_year += amount

        except:
            pass

    return render_template(
        "analytics.html",

        labels=labels,
        amounts=amounts,

        dist_labels=dist_labels,
        dist_amounts=dist_amounts,

        week_now=week_now,
        week_last=week_last,

        month_now=month_now,
        month_last=month_last,

        year_now=year_now,
        year_last=year_last,

        distribution_this_week=distribution_this_week,
        distribution_last_week=distribution_last_week,

        distribution_this_month=distribution_this_month,
        distribution_last_month=distribution_last_month,

        distribution_this_year=distribution_this_year,
        distribution_last_year=distribution_last_year
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

    # ADD RECOVERY
if request.method == "POST":

    day = request.form["day"]
    amount = request.form["amount"]

    c.execute(
        "INSERT INTO analytics(day,amount) VALUES(?,?)",
        (day, amount)
    )

    conn.commit()

    return redirect("/admin")
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    distributions = c.fetchall()

    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        data=data,
        distributions=distributions,
        users=users
    )


# =========================
# ADD USER (FIXED)
# =========================
@app.route("/add-user", methods=["POST"])
def add_user():
    if "user" not in session:
        return redirect("/login")

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return "User already exists"

    c.execute("INSERT INTO users(username,password) VALUES(?,?)",
              (username, password))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# ADD DISTRIBUTION (FIXED)
# =========================
@app.route("/add-distribution", methods=["POST"])
def add_distribution():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO distribution(day,amount) VALUES(?,?)",
              (request.form["day"], request.form["amount"]))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE
# =========================
@app.route("/delete-recovery/<int:id>")
def delete_recovery(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM analytics WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/delete-distribution/<int:id>")
def delete_distribution(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM distribution WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/delete-user/<int:id>")
def delete_user(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE id=?", (id,))
    user = c.fetchone()

    if user and user[0] == "rawishtahir":
        return "Admin Protected"

    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)
