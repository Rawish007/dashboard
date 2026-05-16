from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# DATABASE
conn = sqlite3.connect("database.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS analytics(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    amount INTEGER
)
""")

conn.commit()
conn.close()


@app.route("/")
def dashboard():

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

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    current_week = today.isocalendar()[1]
    last_week_number = current_week - 1

    current_month = today.month
    last_month_number = current_month - 1

    current_year = today.year

    best_day = 0
    worst_day = 999999999

    for row in data:

        amount = row[2]
        date = datetime.strptime(row[1], "%Y-%m-%d").date()

        total += amount

        labels.append(row[1])
        amounts.append(amount)

        # TODAY
        if date == today:
            today_total += amount

        # YESTERDAY
        if date == yesterday:
            yesterday_total += amount

        # THIS WEEK
        if date.isocalendar()[1] == current_week:
            this_week += amount

        # LAST WEEK
        if date.isocalendar()[1] == last_week_number:
            last_week += amount

        # THIS MONTH
        if date.month == current_month:
            this_month += amount

        # LAST MONTH
        if date.month == last_month_number:
            last_month += amount

        # THIS YEAR
        if date.year == current_year:
            this_year += amount

        # BEST DAY
        if amount > best_day:
            best_day = amount

        # WORST DAY
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


@app.route("/admin", methods=["GET", "POST"])
def admin():

    if request.method == "POST":

        day = request.form["day"]
        amount = request.form["amount"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO analytics(day, amount) VALUES(?, ?)",
            (day, amount)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("admin.html")


if __name__ == "__main__":
    app.run(debug=True)
