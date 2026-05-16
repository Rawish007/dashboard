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

    # users table (UPDATED)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # default admin (ONLY ONCE)
    c.execute("SELECT * FROM users WHERE username=?", ("rawish",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users(username, password) VALUES(?,?)",
            ("rawish", "12345")
        )

    conn.commit()
    conn.close()

init_db()


# =========================
# LOGIN (FIXED)
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
            session["user"] = user[1]
            return redirect("/")
        else:
            return "Invalid username or password"

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

    c.execute("SELECT * FROM analytics")
    data = c.fetchall()
    conn.close()

    total = 0
    labels = []
    amounts = []

    today_total = 0
    today = datetime.now().date()

    for row in data:
        amount = int(row[2])
        date = datetime.strptime(row[1], "%Y-%m-%d").date()

        total += amount
        labels.append(row[1])
        amounts.append(amount)

        if date == today:
            today_total += amount

    return render_template(
        "dashboard.html",
        total=total,
        today_total=today_total,
        labels=labels,
        amounts=amounts,
        data=data[::-1]
    )


# =========================
# ADMIN PANEL (USERS + RECOVERY)
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

        c.execute("INSERT INTO analytics(day, amount) VALUES(?, ?)",
                  (day, amount))
        conn.commit()

    # GET USERS
    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html", users=users)


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

    c.execute("INSERT INTO users(username, password) VALUES(?,?)",
              (username, password))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE USER
# =========================
@app.route("/delete-user/<int:id>")
def delete_user(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# CHANGE PASSWORD (ADMIN CONTROL)
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
        return redirect("/admin")
    else:
        conn.close()
        return "Old password wrong"


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
