from flask import Flask, request, render_template, render_template_string
import sqlite3

app = Flask(__name__)

DATABASE = "campus.db"


# ---------------- DATABASE ----------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            item TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            finder TEXT NOT NULL,
            item TEXT NOT NULL,
            location TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------- REPORT LOST ----------------

@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():

    if request.method == "POST":

        name = request.form["name"].strip()
        item = request.form["item"].strip().lower()
        location = request.form["location"].strip()

        conn = get_db()

        conn.execute(
            "INSERT INTO lost_items (name, item, location) VALUES (?, ?, ?)",
            (name, item, location)
        )

        conn.commit()
        conn.close()

        return render_template_string("""
        <h1>✅ Lost Item Reported!</h1>

        <p><b>Name:</b> {{ name }}</p>
        <p><b>Item:</b> {{ item }}</p>
        <p><b>Location:</b> {{ location }}</p>

        <p>💾 Your report has been saved.</p>

        <a href="/">← Back to Home</a>
        """,
        name=name,
        item=item,
        location=location)

    return render_template_string("""
    <h1>🔴 Report Lost Item</h1>

    <form method="POST">

        <label>Your Name:</label><br>
        <input type="text" name="name" required>
        <br><br>

        <label>Item Name:</label><br>
        <input type="text" name="item" required>
        <br><br>

        <label>Lost Location:</label><br>
        <input type="text" name="location" required>
        <br><br>

        <button type="submit">Submit Report</button>

    </form>

    <br>
    <a href="/">← Back to Home</a>
    """)


# ---------------- REPORT FOUND ----------------

@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    if request.method == "POST":

        finder = request.form["finder"].strip()
        item = request.form["item"].strip().lower()
        location = request.form["location"].strip()

        conn = get_db()

        # Save found item
        conn.execute(
            "INSERT INTO found_items (finder, item, location) VALUES (?, ?, ?)",
            (finder, item, location)
        )

        # Find matching lost items
        lost_items = conn.execute(
            "SELECT * FROM lost_items WHERE item = ?",
            (item,)
        ).fetchall()

        matched_names = []

        for lost in lost_items:

            message = (
                f"🔔 Your lost item '{item}' has been found! "
                f"Found at {location}. "
                f"Found by {finder}."
            )

            conn.execute(
                "INSERT INTO notifications (name, message) VALUES (?, ?)",
                (lost["name"], message)
            )

            matched_names.append(lost["name"])

        conn.commit()
        conn.close()

        if matched_names:

            names = ", ".join(matched_names)

            return render_template_string("""
            <h1>🎉 Match Found!</h1>

            <p>The found item matches a lost-item report.</p>

            <h3>🔔 Notification sent to:</h3>

            <p>✅ {{ names }}</p>

            <br>
            <a href="/">← Back to Home</a>
            """,
            names=names)

        else:

            return render_template_string("""
            <h1>ℹ️ No Match Found</h1>

            <p>The found item has been saved.</p>

            <p>We will keep it in the system for future matching.</p>

            <br>
            <a href="/">← Back to Home</a>
            """)

    return render_template_string("""
    <h1>🟢 Report Found Item</h1>

    <form method="POST">

        <label>Your Name:</label><br>
        <input type="text" name="finder" required>
        <br><br>

        <label>Found Item Name:</label><br>
        <input type="text" name="item" required>
        <br><br>

        <label>Found Location:</label><br>
        <input type="text" name="location" required>
        <br><br>

        <button type="submit">Submit Found Item</button>

    </form>

    <br>
    <a href="/">← Back to Home</a>
    """)


# ---------------- NOTIFICATIONS ----------------

@app.route("/notifications")
def show_notifications():

    name = request.args.get("name", "").strip()

    conn = get_db()

    messages = conn.execute(
        "SELECT message FROM notifications WHERE name = ?",
        (name,)
    ).fetchall()

    conn.close()

    return render_template_string("""
    <h1>🔔 Your Notifications</h1>

    {% if messages %}

        {% for message in messages %}
            <p>🟢 {{ message["message"] }}</p>
        {% endfor %}

    {% else %}

        <p>No notifications found for <b>{{ name }}</b>.</p>

    {% endif %}

    <br>
    <a href="/">← Back to Home</a>
    """,
    messages=messages)

# ---------------- DASHBOARD ----------------

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    search = request.args.get("search", "").strip().lower()
    item_type = request.args.get("type", "all")
    location = request.args.get("location", "").strip().lower()

    conn = get_db()

    # Get lost items
    lost_items = conn.execute(
        "SELECT * FROM lost_items ORDER BY id DESC"
    ).fetchall()

    # Get found items
    found_items = conn.execute(
        "SELECT * FROM found_items ORDER BY id DESC"
    ).fetchall()

    conn.close()

    # ---------------- SEARCH + FILTER ----------------

    if search:
        lost_items = [
            x for x in lost_items
            if search in x["item"].lower()
            or search in x["name"].lower()
            or search in x["location"].lower()
        ]

        found_items = [
            x for x in found_items
            if search in x["item"].lower()
            or search in x["finder"].lower()
            or search in x["location"].lower()
        ]

    if location:
        lost_items = [
            x for x in lost_items
            if location in x["location"].lower()
        ]

        found_items = [
            x for x in found_items
            if location in x["location"].lower()
        ]

    if item_type == "lost":
        found_items = []

    elif item_type == "found":
        lost_items = []

    return render_template_string("""
    <!DOCTYPE html>
    <html>

    <head>

        <title>Campus Lost & Found Dashboard</title>

        <style>

            body {
                font-family: Arial;
                background: #eef6ff;
                padding: 30px;
            }

            h1 {
                text-align: center;
                color: #1769aa;
            }

            .search-box {
                background: white;
                padding: 20px;
                max-width: 800px;
                margin: 25px auto;
                border-radius: 12px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.12);
            }

            input, select {
                padding: 12px;
                margin: 5px;
                border: 1px solid #bbb;
                border-radius: 7px;
            }

            button {
                padding: 12px 20px;
                background: #1769aa;
                color: white;
                border: none;
                border-radius: 7px;
                cursor: pointer;
            }

            .stats {
                display: flex;
                gap: 20px;
                justify-content: center;
                margin: 25px;
            }

            .box {
                background: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                min-width: 150px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.12);
            }

            .items {
                background: white;
                padding: 20px;
                margin: 20px auto;
                max-width: 800px;
                border-radius: 12px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.12);
            }

            .lost {
                border-left: 6px solid #e53935;
            }

            .found {
                border-left: 6px solid #2e7d32;
            }

            a {
                text-decoration: none;
                color: #1769aa;
            }

        </style>

    </head>

    <body>

        <h1>📊 Campus Lost & Found Dashboard</h1>


        <!-- SEARCH + FILTER -->

        <div class="search-box">

            <form method="GET" action="/dashboard">

                <input
                    type="text"
                    name="search"
                    placeholder="🔍 Search item, name or location"
                    value="{{ search }}"
                >

                <input
                    type="text"
                    name="location"
                    placeholder="📍 Filter by location"
                    value="{{ location }}"
                >

                <select name="type">

                    <option value="all"
                        {% if item_type == "all" %}selected{% endif %}>
                        All Items
                    </option>

                    <option value="lost"
                        {% if item_type == "lost" %}selected{% endif %}>
                        🔴 Lost Items
                    </option>

                    <option value="found"
                        {% if item_type == "found" %}selected{% endif %}>
                        🟢 Found Items
                    </option>

                </select>

                <button type="submit">
                    🔍 Search
                </button>

            </form>

        </div>


        <!-- LOST ITEMS -->

        <div class="items lost">

            <h2>🔴 Lost Items ({{ lost_items|length }})</h2>

            {% if lost_items %}

                {% for item in lost_items %}

                    <p>
                        <b>{{ item["item"] }}</b><br>
                        👤 {{ item["name"] }}<br>
                        📍 {{ item["location"] }}
                    </p>

                    <hr>

                {% endfor %}

            {% else %}

                <p>No lost items found.</p>

            {% endif %}

        </div>


        <!-- FOUND ITEMS -->

        <div class="items found">

            <h2>🟢 Found Items ({{ found_items|length }})</h2>

            {% if found_items %}

                {% for item in found_items %}

                    <p>
                        <b>{{ item["item"] }}</b><br>
                        👤 Found by {{ item["finder"] }}<br>
                        📍 {{ item["location"] }}
                    </p>

                    <hr>

                {% endfor %}

            {% else %}

                <p>No found items found.</p>

            {% endif %}

        </div>


        <center>

            <a href="/">← Back to Home</a>

        </center>

    </body>

    </html>
    """,
    lost_items=lost_items,
    found_items=found_items,
    search=search,
    location=location,
    item_type=item_type
    )
# ---------------- START DATABASE + APP ----------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)