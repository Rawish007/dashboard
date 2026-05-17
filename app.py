from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "umeedsecret"


# =========================
# DB INIT
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
        c.execute("INSERT INTO users(username,password) VALUES(?,?)",
                  ("admin", "admin123"))

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

        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (request.form["username"], request.form["password"]))

        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            return redirect("/admin")

        return render_template("login.html", error="Invalid login")

    return render_template("login.html")


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


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
            (request.form["day"], request.form["amount"])
        )
        conn.commit()
        return redirect("/admin")

    # DATA
    c.execute("SELECT * FROM analytics ORDER BY id DESC")
    data = c.fetchall()

    c.execute("SELECT * FROM distribution ORDER BY id DESC")
    distributions = c.fetchall()

    c.execute("SELECT * FROM users ORDER BY id DESC")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html",
                           data=data,
                           distributions=distributions,
                           users=users)


# =========================
# ADD DISTRIBUTION
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
# ADD USER
# =========================
@app.route("/add-user", methods=["POST"])
def add_user():

    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("INSERT INTO users(username,password) VALUES(?,?)",
              (request.form["username"], request.form["password"]))

    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE RECOVERY
# =========================
@app.route("/delete-recovery/<int:id>")
def delete_recovery(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM analytics WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")


# =========================
# DELETE DISTRIBUTION
# =========================
@app.route("/delete-distribution/<int:id>")
def delete_distribution(id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM distribution WHERE id=?", (id,))
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


if __name__ == "__main__":
    app.run(debug=True)
