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

    # ANALYTICS TABLE
    c.execute("""
    CREATE TABLE IF NOT EXISTS analytics(
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
    count = c.fetchone()[0]

    if count == 0:
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

    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    conn.close()

    total = 0
    today_total = 0
    yesterday_total = 0

    this_week = 0
    last_week = 0

    this_month = 0
    last_month = 0

    best_day = 0

    labels = []
    amounts = []

    filter_days = request.args.get("filter")

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    current_year = today.year

    current_month = today.month

    if current_month == 1:
        previous_month = 12
        previous_month_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_month_year = current_year

    for row in data:

        try:
            amount = int(row[2])

            date = datetime.strptime(row[1], "%Y-%m-%d").date()

            if filter_days:
                limit_date = today - timedelta(days=int(filter_days))
                if date < limit_date:
                    continue

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

            if date.isocalendar()[1] == current_week - 1 and date.year == current_year:
                last_week += amount

            if date.month == current_month and date.year == current_year:
                this_month += amount

            if date.month == previous_month and date.year == previous_month_year:
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
# ANALYTICS (FIXED HERE 👇)
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

    labels = []
    amounts = []

    for row in data:
        labels.append(row[1])
        amounts.append(row[2])

    return render_template(
        "analytics.html",
        labels=labels,
        amounts=amounts,
        data=data
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

        day = request.form["day"]
        amount = request.form["amount"]

        c.execute(
            "INSERT INTO analytics(day,amount) VALUES(?,?)",
            (day, amount)
        )

        conn.commit()

    # RECOVERY DATA
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    # USERS
    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        users=users,
        data=data
    )


# =========================
# ADD USER
# =========================
@app.route("/add-user", methods=["POST"])
def add_user():

    if "user" not in session:
        return redirect("/login")

    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        (username, password)
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
# DELETE USER
# =========================
@app.route("/delete-user/<int:id>")
def delete_user(id):

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # USER CHECK
    c.execute(
        "SELECT username FROM users WHERE id=?",
        (id,)
    )

    user = c.fetchone()

    # MAIN ADMIN PROTECTION
    if user and user[0] == "rawishtahir":

        conn.close()

        return """
        <h2 style='font-family:sans-serif;
        color:red;
        padding:40px;'>
        Main Admin Cannot Be Deleted 🔒
        </h2>
        """

    # DELETE USER
    c.execute(
        "DELETE FROM users WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":

    app.run(debug=True)
