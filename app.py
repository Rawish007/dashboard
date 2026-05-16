from flask import Flask, render_template, request, redirect, session
import sqlite3

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

    # users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    # ✅ NEW ADMIN LOGIN SET
    c.execute("SELECT * FROM users WHERE username=?", ("rawishtahir",))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users(username, password) VALUES(?,?)",
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
            return "Invalid login"

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

    total = sum(int(i[2]) for i in data)

    return render_template(
        "dashboard.html",
        total=total,
        data=data[::-1]
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

    if request.method == "POST":
        day = request.form["day"]
        amount = request.form["amount"]

        c.execute(
            "INSERT INTO analytics(day, amount) VALUES(?,?)",
            (day, amount)
        )
        conn.commit()

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

    c.execute(
        "INSERT INTO users(username, password) VALUES(?,?)",
        (username, password)
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

    c.execute("DELETE FROM users WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)
