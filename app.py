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

    # RECOVERY TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )
    """)

    # ✅ DISTRIBUTION TABLE ADDED
    c.execute("""
    CREATE TABLE IF NOT EXISTS distribution(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )
    """)

    # USERS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # DEFAULT ADMIN
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
            return render_template(
                "login.html",
                error="Invalid Login"
            )

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

    # RECOVERY
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    # DISTRIBUTION
    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    distributions = c.fetchall()

    conn.close()

    total = 0
    distribution_total = 0

    today_total = 0
    yesterday_total = 0

    this_week = 0
    last_week = 0

    this_month = 0
    last_month = 0

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

    # RECOVERY LOOP
    for row in data:

        try:

            amount = int(row[2])

            date = datetime.strptime(
                row[1],
                "%Y-%m-%d"
            ).date()

            total += amount

            labels.append(row[1])
            amounts.append(amount)

            if amount > best_day:
                best_day = amount

            if date == today:
                today_total += amount

            if date == yesterday:
                yesterday_total += amount

            if (
                date.isocalendar()[1] == current_week
                and date.year == current_year
            ):
                this_week += amount

            if date.isocalendar()[1] == current_week - 1:
                last_week += amount

            if date.month == current_month:
                this_month += amount

            if (
                date.month == prev_month
                and date.year == prev_month_year
            ):
                last_month += amount

        except:
            pass

    # DISTRIBUTION TOTAL
    for d in distributions:

        try:
            distribution_total += int(d[2])
        except:
            pass

    return render_template(

        "dashboard.html",

        total=total,
        distribution_total=distribution_total,

        today_total=today_total,
        yesterday_total=yesterday_total,

        this_week=this_week,
        last_week=last_week,

        this_month=this_month,
        last_month=last_month,

        best_day=best_day,

        labels=labels,
        amounts=amounts,

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

    conn.close()

    today_val = 0
    yesterday_val = 0
    total_val = 0

    week_now = 0
    week_last = 0

    month_now = 0
    month_last = 0

    year_now = 0
    year_last = 0

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month

    for row in data:

        try:

            amount = int(row[2])

            date = datetime.strptime(
                row[1],
                "%Y-%m-%d"
            ).date()

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
# ADMIN PANEL
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # ADD RECOVERY
    if request.method == "POST":

        c.execute(
            "INSERT INTO analytics(day,amount) VALUES(?,?)",
            (
                request.form["day"],
                request.form["amount"]
            )
        )

        conn.commit()

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
        users=users,
        distributions=distributions
    )

# =========================
# ADD DISTRIBUTION
# =========================
@app.route("/add-distribution", methods=["POST"])
def add_distribution():

    if "user" not in session:
        return redirect("/login")

    day = request.form["day"]
    amount = request.form["amount"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO distribution(day,amount) VALUES(?,?)",
        (day, amount)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")
    

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
        (
            request.form["username"],
            request.form["password"]
        )
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# ADD DISTRIBUTION
# =========================
@app.route("/add-distribution", methods=["POST"])
def add_distribution():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO distribution(day,amount) VALUES(?,?)",
        (
            request.form["day"],
            request.form["amount"]
        )
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

    c.execute(
        "DELETE FROM analytics WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE DISTRIBUTION
# =========================
@app.route("/delete-distribution/<int:id>")
def delete_distribution(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "DELETE FROM distribution WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE USER
# =========================
@app.route("/delete-user/<int:id>")
def delete_user(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "SELECT username FROM users WHERE id=?",
        (id,)
    )

    user = c.fetchone()

    # ADMIN HIDE / PROTECT
    if user and user[0] == "rawishtahir":

        conn.close()

        return """
        <h2 style='color:red;
        font-family:sans-serif;
        padding:30px;'>
        Admin Protected
        </h2>
        """

    c.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# RUN
# =========================
if __name__ == "__main__":

    app.run(debug=True)
