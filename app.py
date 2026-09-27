from flask import Flask, request, render_template, render_template_string, session, redirect
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "campus_lost_found_secret_key"

# Render will provide DATABASE_URL through the environment.
# When running locally without DATABASE_URL, SQLite is used automatically.
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DATABASE = "campus.db"


# ---------------- DATABASE ----------------

def get_db():
    if DATABASE_URL:
        return psycopg2.connect(
            DATABASE_URL,
            cursor_factory=RealDictCursor
        )

    conn = sqlite3.connect(SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def db_execute(conn, query, params=()):
    """Run the same query against SQLite or PostgreSQL."""
    if DATABASE_URL:
        query = query.replace("?", "%s")
        cur = conn.cursor()
        cur.execute(query, params)
        return cur

    return conn.execute(query, params)


def init_db():
    conn = get_db()

    if DATABASE_URL:

        # LOST ITEMS
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS lost_items (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # FOUND ITEMS
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS found_items (
                id SERIAL PRIMARY KEY,
                finder TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # NOTIFICATIONS
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # USERS
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # Add user_id to old tables if they already existed
        conn.cursor().execute("""
            ALTER TABLE lost_items
            ADD COLUMN IF NOT EXISTS user_id INTEGER
        """)

        conn.cursor().execute("""
            ALTER TABLE found_items
            ADD COLUMN IF NOT EXISTS user_id INTEGER
        """)

        conn.cursor().execute("""
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS user_id INTEGER
        """)

    else:

        # LOST ITEMS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lost_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # FOUND ITEMS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finder TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # USERS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        # NOTIFICATIONS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        # Add user_id to old SQLite tables if needed
        tables = {
            "lost_items": "user_id",
            "found_items": "user_id",
            "notifications": "user_id"
        }

        for table, column in tables.items():
            columns = conn.execute(
                f"PRAGMA table_info({table})"
            ).fetchall()

            column_names = [row["name"] for row in columns]

            if column not in column_names:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} INTEGER"
                )

    conn.commit()
    conn.close()


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        user = db_execute(
            conn,
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            session["user_id"] = user["id"]

            return redirect("/dashboard")
        else:
            return render_template_string("""
            <h1>❌ Invalid Username or Password</h1>
            <p>Username or password is incorrect.</p>
            <br>
            <a href="/login">← Try Again</a>
            """)
    return render_template_string("""
    <h1>🔐 Campus Lost & Found Login</h1>

    <form method="POST">

        <label>Username:</label><br>
        <input type="text" name="username" required>

        <br><br>

        <label>Password:</label><br>
        <input type="password" name="password" required>

        <br><br>

        <button type="submit">Login</button>

    </form>

    <br>

    <a href="/register">📝 New user? Register</a>
    <br><br>
    <a href="/forgot-password">🔑 Forgot Password?</a>
    """)


# ---------------- FORGOT PASSWORD ----------------

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        username = request.form["username"].strip()
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return render_template_string("""
            <h1>❌ Passwords Do Not Match</h1>
            <p>New password and confirm password must be the same.</p>
            <br>
            <a href="/forgot-password">← Try Again</a>
            """)

        if not new_password:
            return render_template_string("""
            <h1>❌ Invalid Password</h1>
            <p>Password cannot be empty.</p>
            <br>
            <a href="/forgot-password">← Try Again</a>
            """)

        conn = get_db()

        user = db_execute(
            conn,
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            conn.close()
            return render_template_string("""
            <h1>❌ Username Not Found</h1>
            <p>No account was found with this username.</p>
            <br>
            <a href="/forgot-password">← Try Again</a>
            """)

        password_hash = generate_password_hash(new_password)

        db_execute(
            conn,
            "UPDATE users SET password = ? WHERE username = ?",
            (password_hash, username)
        )

        conn.commit()
        conn.close()

        return render_template_string("""
        <h1>✅ Password Changed Successfully</h1>
        <p>Your password has been updated.</p>
        <br>
        <a href="/login">🔐 Go to Login</a>
        """)

    return render_template_string("""
    <h1>🔑 Forgot Password</h1>

    <form method="POST">

        <label>Username:</label><br>
        <input type="text" name="username" required>

        <br><br>

        <label>New Password:</label><br>
        <input type="password" name="new_password" required>

        <br><br>

        <label>Confirm New Password:</label><br>
        <input type="password" name="confirm_password" required>

        <br><br>

        <button type="submit">Change Password</button>

    </form>

    <br>

    <a href="/login">← Back to Login</a>
    """)


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()

        password_hash = generate_password_hash(password)

        try:
            db_execute(
                conn,
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password_hash)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except Exception as e:
            conn.close()

            return render_template_string("""
            <h1>Registration Error</h1>
            <p>Username may already exist.</p>
            <p>{{ error }}</p>
            <br>
            <a href="/register">← Back to Register</a>
            """, error=str(e))

    return render_template_string("""
    <h1>📝 Campus Lost & Found Register</h1>

    <form method="POST">

        <label>Username:</label><br>
        <input type="text" name="username" required>

        <br><br>

        <label>Password:</label><br>
        <input type="password" name="password" required>

        <br><br>

        <button type="submit">Register</button>

    </form>

    <br>

    <a href="/login">🔐 Already have an account? Login</a>
    """)


# ---------------- HOME ----------------

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html")


# ---------------- REPORT LOST ----------------

@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        name = request.form["name"].strip()
        item = request.form["item"].strip().lower()
        location = request.form["location"].strip()
        contact = request.form["contact"].strip()

        conn = get_db()

        # Save lost item
        db_execute(
            conn,
            """
            INSERT INTO lost_items
            (name, item, location, contact, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                name,
                item,
                location,
                contact,
                session["user_id"]
            )
        )

        # Check already reported found items
        found_items = db_execute(
            conn,
            "SELECT * FROM found_items WHERE LOWER(item) = LOWER(?)",
            (item,)
        ).fetchall()

        matched = False

        for found in found_items:

            # Avoid duplicate notification
            existing = db_execute(
                conn,
                """
                SELECT id
                FROM notifications
                WHERE user_id = ?
                AND message LIKE ?
                LIMIT 1
                """,
                (
                    session["user_id"],
                    f"%Your lost item '{item}' has been found!%"
                )
            ).fetchone()

            if not existing:

                message = (
                    f"🔔 Your lost item '{item}' has been found! "
                    f"Found at {found['location']}. "
                    f"Found by {found['finder']}. "
                    f"📞 Contact: {found['contact']}"
                )

                db_execute(
                    conn,
                    """
                    INSERT INTO notifications
                    (name, message, user_id)
                    VALUES (?, ?, ?)
                    """,
                    (
                        name,
                        message,
                        session["user_id"]
                    )
                )

            matched = True

        conn.commit()
        conn.close()

        if matched:

            return render_template_string("""
            <h1>🎉 Match Found!</h1>

            <p>
                Your lost item matches an item that was already
                reported as found.
            </p>

            <p>
                🔔 A notification has been sent to
                <b>{{ name }}</b>.
            </p>

            <p>
                📱 Check your notifications to see the finder's
                contact number.
            </p>

            <br>

            <a href="/">← Back to Home</a>

            """, name=name)

        return render_template_string("""
        <h1>✅ Lost Item Reported!</h1>

        <p><b>Name:</b> {{ name }}</p>
        <p><b>Item:</b> {{ item }}</p>

        <p>
            💾 Your report has been saved.
        </p>

        <p>
            We will notify you automatically if a matching
            found item is reported.
        </p>

        <br>

        <a href="/">← Back to Home</a>

        """, name=name, item=item)

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

        <label>Contact Number:</label><br>
        <input type="tel" name="contact" required>

        <br><br>

        <button type="submit">
            Submit Report
        </button>

    </form>

    <br>

    <a href="/">← Back to Home</a>

    """)


# ---------------- REPORT FOUND ----------------

@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        finder = request.form["finder"].strip()
        item = request.form["item"].strip()
        location = request.form["location"].strip()
        contact = request.form["contact"].strip()

        conn = get_db()

        # Save found item
        db_execute(
            conn,
            """
            INSERT INTO found_items
            (finder, item, location, contact, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                finder,
                item,
                location,
                contact,
                session["user_id"]
            )
        )

        # Find matching lost reports
        lost_items = db_execute(
            conn,
            """
            SELECT *
            FROM lost_items
            WHERE LOWER(item) = LOWER(?)
            """,
            (item,)
        ).fetchall()

        matched_names = []

        # Create one notification per matching lost report
        for lost in lost_items:

            existing = db_execute(
                conn,
                """
                SELECT id
                FROM notifications
                WHERE user_id = ?
                AND message LIKE ?
                LIMIT 1
                """,
                (
                    lost["user_id"],
                    f"%Your lost item '{item}' has been found!%"
                )
            ).fetchone()

            if not existing:

                message = (
                    f"🔔 Your lost item '{item}' has been found! "
                    f"Found at {location}. "
                    f"Found by {finder}. "
                    f"📞 Contact: {contact}"
                )

                db_execute(
                    conn,
                    """
                    INSERT INTO notifications
                    (name, message, user_id)
                    VALUES (?, ?, ?)
                    """,
                    (
                        lost["name"],
                        message,
                        lost["user_id"]
                    )
                )

            matched_names.append(lost["name"])

        conn.commit()
        conn.close()

        if matched_names:

            names = ", ".join(
                dict.fromkeys(matched_names)
            )

            # Do NOT show the finder's phone number to the finder.
            # The contact number is available to the matched
            # lost reporter through their notification.

            return render_template_string("""
            <h1>🎉 Match Found!</h1>

            <p>
                The found item matches a lost-item report.
            </p>

            <h3>🔔 Notification sent to:</h3>

            <p>✅ {{ names }}</p>

            <p>
                📱 The matched user can see your contact
                number in their notification.
            </p>

            <br>

            <a href="/">← Back to Home</a>

            """, names=names)

        return render_template_string("""
        <h1>ℹ️ No Match Found</h1>

        <p>
            The found item has been saved.
        </p>

        <p>
            We will keep it in the system for future matching.
        </p>

        <br>

        <a href="/">← Back to Home</a>

        """)

    # GET request
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

        <label>Contact Number:</label><br>
        <input type="tel" name="contact" required>

        <br><br>

        <button type="submit">
            Submit Found Item
        </button>

    </form>

    <br>

    <a href="/">← Back to Home</a>

    """)


# ---------------- NOTIFICATIONS ----------------

@app.route("/notifications")
def show_notifications():

    if "user_id" not in session:
        return redirect("/login")

    name = session["username"]

    conn = get_db()

    messages = db_execute(
        conn,
        """
        SELECT message
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template_string("""
    <h1>🔔 Your Notifications</h1>

    {% if messages %}

        {% for message in messages %}

            <p>
                🟢 {{ message["message"] }}
            </p>

        {% endfor %}

    {% else %}

        <p>
            No notifications found for
            <b>{{ name }}</b>.
        </p>

    {% endif %}

    <br>

    <a href="/">← Back to Home</a>

    """,
    messages=messages,
    name=name
    )


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get(
        "search",
        ""
    ).strip().lower()

    item_type = request.args.get(
        "type",
        "all"
    )

    location = request.args.get(
        "location",
        ""
    ).strip().lower()

    conn = get_db()

    # Only logged-in user's lost reports
    lost_items = db_execute(
        conn,
        """
        SELECT *
        FROM lost_items
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    # Only logged-in user's found reports
    found_items = db_execute(
        conn,
        """
        SELECT *
        FROM found_items
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    ).fetchall()

    conn.close()

    # Search
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

    # Location filter
    if location:

        lost_items = [
            x for x in lost_items
            if location in x["location"].lower()
        ]

        found_items = [
            x for x in found_items
            if location in x["location"].lower()
        ]

    # Type filter
    if item_type == "lost":

        found_items = []

    elif item_type == "found":

        lost_items = []

    return render_template_string("""
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            Campus Lost & Found Dashboard
        </title>

        <style>

            body {
                font-family: Arial, sans-serif;
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
                box-shadow:
                    0 3px 10px
                    rgba(0,0,0,0.12);
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
                flex-wrap: wrap;
            }

            .box {
                background: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                min-width: 150px;
                box-shadow:
                    0 3px 10px
                    rgba(0,0,0,0.12);
            }

            .items {
                background: white;
                padding: 20px;
                margin: 20px auto;
                max-width: 800px;
                border-radius: 12px;
                box-shadow:
                    0 3px 10px
                    rgba(0,0,0,0.12);
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

        <h1>
            📊 Campus Lost & Found Dashboard
        </h1>

        <div class="stats">

            <div class="box">

                <h3>🔴 Lost</h3>

                <p>
                    {{ lost_items|length }}
                </p>

            </div>

            <div class="box">

                <h3>🟢 Found</h3>

                <p>
                    {{ found_items|length }}
                </p>

            </div>

        </div>


        <!-- SEARCH + FILTER -->

        <div class="search-box">

            <form
                method="GET"
                action="/dashboard"
            >

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

                    <option
                        value="all"
                        {% if item_type == "all" %}
                        selected
                        {% endif %}
                    >
                        All Items
                    </option>

                    <option
                        value="lost"
                        {% if item_type == "lost" %}
                        selected
                        {% endif %}
                    >
                        🔴 Lost Items
                    </option>

                    <option
                        value="found"
                        {% if item_type == "found" %}
                        selected
                        {% endif %}
                    >
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

            <h2>
                🔴 Lost Items
                ({{ lost_items|length }})
            </h2>

            {% if lost_items %}

                {% for item in lost_items %}

                    <p>

                        <b>
                            {{ item["item"] }}
                        </b>

                        <br>

                        👤 {{ item["name"] }}

                        <br>

                        📍 {{ item["location"] }}

                    </p>

                    <hr>

                {% endfor %}

            {% else %}

                <p>
                    No lost items found.
                </p>

            {% endif %}

        </div>


        <!-- FOUND ITEMS -->

        <div class="items found">

            <h2>
                🟢 Found Items
                ({{ found_items|length }})
            </h2>

            {% if found_items %}

                {% for item in found_items %}

                    <p>

                        <b>
                            {{ item["item"] }}
                        </b>

                        <br>

                        👤 Found by
                        {{ item["finder"] }}

                        <br>

                        📍 {{ item["location"] }}

                    </p>

                    <hr>

                {% endfor %}

            {% else %}

                <p>
                    No found items found.
                </p>

            {% endif %}

        </div>


        <center>

            <a href="/">
                ← Back to Home
            </a>

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

init_db()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)