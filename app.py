from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import hashlib
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "umeedsecret-change-in-production"


# =========================
# HELPERS
# =========================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated

def compute_stats(rows, today, yesterday, current_week, current_year, current_month, prev_month, prev_month_year):
    """Compute all time-period stats for a set of (day, amount) rows."""
    total = today_val = yesterday_val = 0
    this_week = last_week = 0
    this_month = last_month = 0
    this_year = last_year = 0
    best_day = 0
    labels = []
    amounts = []

    for row in rows:
        try:
            amount = int(row["amount"])
            date = datetime.strptime(row["day"], "%Y-%m-%d").date()

            total += amount
            labels.append(row["day"])
            amounts.append(amount)
            best_day = max(best_day, amount)

            if date == today:
                today_val += amount
            if date == yesterday:
                yesterday_val += amount
            if date.isocalendar()[1] == current_week and date.year == current_year:
                this_week += amount
            if date.isocalendar()[1] == current_week - 1 and date.year == current_year:
                last_week += amount
            if date.month == current_month and date.year == current_year:
                this_month += amount
            if date.month == prev_month and date.year == prev_month_year:
                last_month += amount
            if date.year == current_year:
                this_year += amount
            if date.year == current_year - 1:
                last_year += amount
        except (ValueError, TypeError):
            pass

    return dict(
        total=total,
        today_val=today_val,
        yesterday_val=yesterday_val,
        this_week=this_week,
        last_week=last_week,
        this_month=this_month,
        last_month=last_month,
        this_year=this_year,
        last_year=last_year,
        best_day=best_day,
        labels=labels,
        amounts=amounts,
    )


# =========================
# DATABASE INIT
# =========================
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS distribution(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT,
        amount INTEGER
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )""")

    c.execute("SELECT COUNT(*) as cnt FROM users")
    if c.fetchone()["cnt"] == 0:
        c.execute(
            "INSERT INTO users(username, password) VALUES(?, ?)",
            ("rawishtahir", hash_password("RAWiSH786rawi@"))
        )

    conn.commit()
    conn.close()


init_db()


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect("/")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_password(password))
        )
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user["username"]
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# DATE HELPERS
# =========================
def get_date_context():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    current_week = today.isocalendar()[1]
    current_year = today.year
    current_month = today.month
    prev_month = 12 if current_month == 1 else current_month - 1
    prev_month_year = current_year - 1 if current_month == 1 else current_year
    return today, yesterday, current_week, current_year, current_month, prev_month, prev_month_year


# =========================
# DASHBOARD
# =========================
@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()
    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    distributions = c.fetchall()
    conn.close()

    ctx = get_date_context()
    rec = compute_stats(data, *ctx)
    dist = compute_stats(distributions, *ctx)

    return render_template(
        "dashboard.html",
        # recovery
        total=rec["total"],
        today_total=rec["today_val"],
        yesterday_total=rec["yesterday_val"],
        this_week=rec["this_week"],
        last_week=rec["last_week"],
        this_month=rec["this_month"],
        last_month=rec["last_month"],
        best_day=rec["best_day"],
        labels=rec["labels"],
        amounts=rec["amounts"],
        # distribution
        distribution_total=dist["total"],
        distribution_today=dist["today_val"],
        distribution_yesterday=dist["yesterday_val"],
        distribution_this_week=dist["this_week"],
        distribution_last_week=dist["last_week"],
        distribution_this_month=dist["this_month"],
        distribution_last_month=dist["last_month"],
        best_distribution=dist["best_day"],
        dist_labels=dist["labels"],
        dist_amounts=dist["amounts"],
        data=data,
        distributions=distributions,
    )


# =========================
# ANALYTICS
# =========================
@app.route("/analytics")
@login_required
def analytics():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()
    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    dist_data = c.fetchall()
    conn.close()

    ctx = get_date_context()
    rec = compute_stats(data, *ctx)
    dist = compute_stats(dist_data, *ctx)

    return render_template(
        "analytics.html",
        # recovery stats
        today_val=rec["today_val"],
        yesterday_val=rec["yesterday_val"],
        total_val=rec["total"],
        week_now=rec["this_week"],
        week_last=rec["last_week"],
        month_now=rec["this_month"],
        month_last=rec["last_month"],
        year_now=rec["this_year"],
        year_last=rec["last_year"],
        labels=rec["labels"],
        amounts=rec["amounts"],
        # distribution stats
        distribution_total=dist["total"],
        distribution_today=dist["today_val"],
        distribution_yesterday=dist["yesterday_val"],
        distribution_this_week=dist["this_week"],
        distribution_last_week=dist["last_week"],
        distribution_this_month=dist["this_month"],
        distribution_last_month=dist["last_month"],
        distribution_this_year=dist["this_year"],
        distribution_last_year=dist["last_year"],
        dist_labels=dist["labels"],
        dist_amounts=dist["amounts"],
        data=data,
        dist=dist_data,
    )


# =========================
# ADMIN
# =========================
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        day = request.form.get("day", "").strip()
        amount = request.form.get("amount", "").strip()
        if day and amount:
            try:
                int(amount)
                c.execute(
                    "INSERT INTO analytics(day, amount) VALUES(?, ?)",
                    (day, amount)
                )
                conn.commit()
            except ValueError:
                pass
        conn.close()
        return redirect("/admin")

    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT * FROM distribution ORDER BY id DESC")   # FIX: was 'distributions'
    distributions = c.fetchall()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        data=data,
        distributions=distributions,
        users=users,
    )


# =========================
# ADD USER
# =========================
@app.route("/add-user", methods=["POST"])
@login_required
def add_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    if username and password:
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users(username, password) VALUES(?, ?)",
                (username, hash_password(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # username already exists
        conn.close()

    return redirect("/admin")


# =========================
# ADD DISTRIBUTION
# =========================
@app.route("/add-distribution", methods=["POST"])
@login_required
def add_distribution():
    day = request.form.get("day", "").strip()
    amount = request.form.get("amount", "").strip()

    if day and amount:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO distribution(day, amount) VALUES(?, ?)",
            (day, amount)
        )
        conn.commit()
        conn.close()

    return redirect("/admin")


# =========================
# DELETE FUNCTIONS
# =========================
@app.route("/delete-recovery/<int:id>")
@login_required
def delete_recovery(id):
    conn = get_db()
    conn.execute("DELETE FROM analytics WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/delete-distribution/<int:id>")
@login_required
def delete_distribution(id):
    conn = get_db()
    conn.execute("DELETE FROM distribution WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/delete-user/<int:id>")
@login_required
def delete_user(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE id=?", (id,))
    user = c.fetchone()
    if user and user["username"] == "rawishtahir":
        conn.close()
        return "Admin user is protected.", 403
    conn.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
