@app.route("/")
def dashboard():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM analytics")
    data = c.fetchall()

    total = sum([row[2] for row in data])

    today = datetime.now().strftime("%Y-%m-%d")

    today_total = sum(
        row[2] for row in data
        if row[1] == today
    )

    total_entries = len(data)

    labels = [row[1] for row in data]
    amounts = [row[2] for row in data]

    conn.close()

    return render_template(
        "dashboard.html",

        total=total,
        today_total=today_total,
        total_entries=total_entries,

        labels=labels,
        amounts=amounts,
        data=data[::-1]
    )
