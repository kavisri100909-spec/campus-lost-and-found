from flask import Flask, request, render_template, render_template_string, session, redirect
import os
import re
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "campus_lost_found_secret_key")

# Render provides DATABASE_URL in production.
# Locally, SQLite is used automatically.
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DATABASE = "campus.db"


# ============================================================
# SHARED UI
# ============================================================

APP_CSS = """
:root{
    --blue:#2563eb;
    --blue-dark:#1d4ed8;
    --purple:#7c3aed;
    --ink:#0f172a;
    --muted:#64748b;
    --line:#dbeafe;
    --card:#ffffff;
    --bg:#f4f7ff;
    --danger:#ef476f;
    --success:#16b981;
    --shadow:0 18px 45px rgba(37,99,235,.12);
}

*{box-sizing:border-box;margin:0;padding:0}

body{
    font-family:Inter,Segoe UI,Arial,sans-serif;
    background:
        radial-gradient(circle at 10% 10%, rgba(147,197,253,.45), transparent 30%),
        radial-gradient(circle at 90% 85%, rgba(196,181,253,.38), transparent 28%),
        linear-gradient(135deg,#eef7ff 0%,#f7f3ff 48%,#eef8ff 100%);
    color:var(--ink);
    min-height:100vh;
}

a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}

.app-wrap{
    width:min(100%, 480px);
    min-height:100vh;
    margin:auto;
    padding:18px;
}

.page-card{
    background:rgba(255,255,255,.90);
    backdrop-filter:blur(14px);
    border:1px solid rgba(255,255,255,.8);
    border-radius:30px;
    box-shadow:var(--shadow);
    overflow:hidden;
}

.brand-head{
    padding:28px 24px 24px;
    background:linear-gradient(135deg,var(--blue),var(--purple));
    color:#fff;
    position:relative;
}

.brand-row{display:flex;align-items:center;gap:12px}
.brand-icon{
    width:52px;height:52px;border-radius:18px;
    background:rgba(255,255,255,.18);
    display:grid;place-items:center;font-size:28px;
}
.brand-title{font-size:22px;font-weight:800;line-height:1.1}
.brand-sub{margin-top:5px;font-size:13px;opacity:.9}

.page-body{padding:24px}

.form-card,.result-card,.info-card{
    background:#fff;
    border:1px solid #e5edff;
    border-radius:22px;
    padding:22px;
    box-shadow:0 10px 30px rgba(15,23,42,.06);
}

.page-title{font-size:27px;font-weight:800;margin-bottom:6px}
.page-subtitle{color:var(--muted);font-size:14px;line-height:1.5;margin-bottom:20px}

label{
    display:block;
    font-size:13px;
    font-weight:700;
    margin:14px 0 7px;
}

input,select,textarea{
    width:100%;
    border:1px solid #d8e1f0;
    background:#f9fbff;
    border-radius:14px;
    padding:13px 14px;
    outline:none;
    font-size:15px;
    color:var(--ink);
}
input:focus,select:focus,textarea:focus{
    border-color:#7aa2ff;
    box-shadow:0 0 0 4px rgba(37,99,235,.10);
}
textarea{min-height:110px;resize:vertical}

.btn{
    display:flex;
    align-items:center;
    justify-content:center;
    gap:8px;
    width:100%;
    border:0;
    border-radius:14px;
    padding:14px 16px;
    margin-top:16px;
    font-size:15px;
    font-weight:800;
    cursor:pointer;
    text-decoration:none;
    transition:.18s ease;
}
.btn:hover{text-decoration:none;transform:translateY(-1px)}
.btn-primary{
    color:#fff;
    background:linear-gradient(135deg,var(--blue),var(--purple));
    box-shadow:0 12px 24px rgba(67,56,202,.18);
}
.btn-soft{
    color:#23406f;
    background:#edf4ff;
}
.btn-danger{
    color:#fff;
    background:linear-gradient(135deg,#f43f5e,#e11d48);
}
.btn-success{
    color:#fff;
    background:linear-gradient(135deg,#10b981,#059669);
}

.link-row{
    text-align:center;
    margin-top:18px;
    font-size:14px;
}
.link-row a{font-weight:700}

.alert{
    border-radius:14px;
    padding:12px 14px;
    margin-bottom:16px;
    font-size:14px;
    line-height:1.4;
}
.alert-error{background:#fff1f2;color:#be123c;border:1px solid #fecdd3}
.alert-success{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0}
.alert-info{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}

.back{
    display:inline-flex;
    align-items:center;
    gap:6px;
    margin-top:18px;
    font-weight:700;
    font-size:14px;
}

.section-title{font-size:18px;font-weight:800;margin-bottom:8px}
.section-copy{color:var(--muted);font-size:14px;line-height:1.5}

.stat-grid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:12px;
    margin:16px 0;
}
.stat{
    padding:16px;
    border-radius:20px;
    background:linear-gradient(145deg,#ffffff,#f4f7ff);
    border:1px solid #e4ebff;
}
.stat small{display:block;color:var(--muted);font-weight:700}
.stat strong{display:block;font-size:28px;margin-top:5px}

.item{
    padding:16px;
    border-radius:18px;
    background:#fff;
    border:1px solid #e7edf8;
    margin-top:12px;
}
.item.lost{border-left:5px solid var(--danger)}
.item.found{border-left:5px solid var(--success)}
.item-title{font-weight:800;font-size:16px}
.meta{color:var(--muted);font-size:13px;margin-top:5px;line-height:1.5}

.nav-grid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:12px;
    margin-top:14px;
}
.nav-tile{
    border-radius:20px;
    padding:16px;
    font-weight:800;
    border:1px solid #e3eaff;
    background:#fff;
}
.nav-tile small{display:block;color:var(--muted);font-weight:600;margin-top:5px}
.nav-tile.pink{background:linear-gradient(145deg,#fff0f5,#ffffff)}
.nav-tile.blue{background:linear-gradient(145deg,#eef5ff,#ffffff)}
.nav-tile.green{background:linear-gradient(145deg,#ecfdf5,#ffffff)}
.nav-tile.purple{background:linear-gradient(145deg,#f5f3ff,#ffffff)}

.bottom{
    margin-top:20px;
    padding:16px 8px 4px;
    text-align:center;
    color:#7b879c;
    font-size:12px;
}

@media(max-width:420px){
    .app-wrap{padding:10px}
    .page-card{border-radius:24px}
    .page-body{padding:18px}
}
"""

def styled_page(content, title="Campus Lost & Found", **context):
    rendered_content = render_template_string(content, **context)
    shell = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>{{ css|safe }}</style>
    </head>
    <body>
        <div class="app-wrap">
            <div class="page-card">
                <div class="brand-head">
                    <div class="brand-row">
                        <div class="brand-icon">🎒</div>
                        <div>
                            <div class="brand-title">Campus Lost &amp; Found</div>
                            <div class="brand-sub">Find · Report · Reunite 💙</div>
                        </div>
                    </div>
                </div>
                <div class="page-body">
                    {{ content|safe }}
                </div>
            </div>
            <div class="bottom">🏫 Campus Lost &amp; Found · Built for campus community</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(shell, title=title, css=APP_CSS, content=rendered_content)


# ============================================================
# DATABASE
# ============================================================

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
    """Run the same parameter style against SQLite or PostgreSQL."""
    if DATABASE_URL:
        query = query.replace("?", "%s")
        cur = conn.cursor()
        cur.execute(query, params)
        return cur
    return conn.execute(query, params)


def items_match(item_a, item_b):
    """Check whether two item descriptions have meaningful keyword overlap."""
    a_words = set(re.findall(r"[a-z0-9]+", item_a.lower()))
    b_words = set(re.findall(r"[a-z0-9]+", item_b.lower()))

    # Ignore very common/generic words that are not useful for matching.
    stop_words = {
        "the", "a", "an", "my", "this", "that", "and", "or",
        "item", "lost", "found"
    }
    a_words -= stop_words
    b_words -= stop_words

    return bool(a_words & b_words)


def init_db():
    conn = get_db()

    if DATABASE_URL:
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

        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER
            )
        """)

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


# ============================================================
# LOGIN
# ============================================================

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
            return redirect("/")

        return styled_page("""
            <div class="form-card">
                <div class="page-title">❌ Login Failed</div>
                <div class="page-subtitle">The username or password you entered is incorrect.</div>
                <div class="alert alert-error">
                    Please check your credentials and try again.
                </div>
                <a class="btn btn-primary" href="/login">🔐 Try Again</a>
                <div class="link-row">
                    <a href="/forgot-password">🔑 Forgot Password?</a>
                </div>
            </div>
        """, title="Login Error")

    return styled_page("""
        <div class="form-card">
            <div class="page-title">Welcome Back! 👋</div>
            <div class="page-subtitle">Login to continue to your campus Lost &amp; Found account.</div>

            <form method="POST">
                <label>Username</label>
                <input type="text" name="username" placeholder="Enter your username" required>

                <label>Password</label>
                <input type="password" name="password" placeholder="Enter your password" required>

                <button class="btn btn-primary" type="submit">🔐 Login</button>
            </form>

            <div class="link-row">
                New user? <a href="/register">Create an account</a>
            </div>
            <div class="link-row">
                <a href="/forgot-password">🔑 Forgot Password?</a>
            </div>
        </div>
    """, title="Login")


# ============================================================
# FORGOT PASSWORD
# ============================================================

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"].strip()
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not new_password:
            return styled_page("""
                <div class="form-card">
                    <div class="page-title">❌ Invalid Password</div>
                    <div class="alert alert-error">Password cannot be empty.</div>
                    <a class="btn btn-soft" href="/forgot-password">← Try Again</a>
                </div>
            """, title="Forgot Password")

        if new_password != confirm_password:
            return styled_page("""
                <div class="form-card">
                    <div class="page-title">❌ Passwords Do Not Match</div>
                    <div class="alert alert-error">
                        New password and confirm password must be the same.
                    </div>
                    <a class="btn btn-soft" href="/forgot-password">← Try Again</a>
                </div>
            """, title="Forgot Password")

        conn = get_db()
        user = db_execute(
            conn,
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            conn.close()
            return styled_page("""
                <div class="form-card">
                    <div class="page-title">❌ Username Not Found</div>
                    <div class="alert alert-error">
                        No account was found with this username.
                    </div>
                    <a class="btn btn-soft" href="/forgot-password">← Try Again</a>
                </div>
            """, title="Forgot Password")

        password_hash = generate_password_hash(new_password)
        db_execute(
            conn,
            "UPDATE users SET password = ? WHERE username = ?",
            (password_hash, username)
        )
        conn.commit()
        conn.close()

        return styled_page("""
            <div class="result-card">
                <div class="page-title">✅ Password Changed!</div>
                <div class="page-subtitle">Your new password has been saved successfully.</div>
                <div class="alert alert-success">
                    You can now login with your username and new password.
                </div>
                <a class="btn btn-primary" href="/login">🔐 Go to Login</a>
            </div>
        """, title="Password Updated")

    return styled_page("""
        <div class="form-card">
            <div class="page-title">Forgot Password? 🔑</div>
            <div class="page-subtitle">
                Enter your username and choose a new password.
            </div>

            <form method="POST">
                <label>Username</label>
                <input type="text" name="username" placeholder="Your username" required>

                <label>New Password</label>
                <input type="password" name="new_password" placeholder="Create a new password" required>

                <label>Confirm New Password</label>
                <input type="password" name="confirm_password" placeholder="Repeat the new password" required>

                <button class="btn btn-primary" type="submit">🔑 Change Password</button>
            </form>

            <div class="link-row">
                <a href="/login">← Back to Login</a>
            </div>
        </div>
    """, title="Forgot Password")


# ============================================================
# REGISTER
# ============================================================

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
            return styled_page("""
                <div class="form-card">
                    <div class="page-title">❌ Registration Error</div>
                    <div class="alert alert-error">
                        Username may already exist.
                    </div>
                    <details>
                        <summary>Technical details</summary>
                        <p class="meta">{{ error }}</p>
                    </details>
                    <a class="btn btn-soft" href="/register">← Back to Register</a>
                </div>
            """, title="Registration Error", error=str(e))

    return styled_page("""
        <div class="form-card">
            <div class="page-title">Create Account 📝</div>
            <div class="page-subtitle">
                Join Campus Lost &amp; Found to report and track items.
            </div>

            <form method="POST">
                <label>Username</label>
                <input type="text" name="username" placeholder="Choose a username" required>

                <label>Password</label>
                <input type="password" name="password" placeholder="Create a password" required>

                <button class="btn btn-primary" type="submit">📝 Register</button>
            </form>

            <div class="link-row">
                Already have an account? <a href="/login">Login</a>
            </div>
        </div>
    """, title="Register")


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("index.html", username=session.get("username", "User"))


# ============================================================
# REPORT LOST
# ============================================================

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

        db_execute(
            conn,
            """
            INSERT INTO lost_items
            (name, item, location, contact, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, item, location, contact, session["user_id"])
        )

        all_found_items = db_execute(
            conn,
            "SELECT * FROM found_items"
        ).fetchall()

        found_items = [
            found for found in all_found_items
            if items_match(item, found["item"])
        ]

        matched = False

        for found in found_items:
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
                    (name, message, session["user_id"])
                )

            matched = True

        conn.commit()
        conn.close()

        if matched:
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">🎉 Match Found!</div>
                    <div class="page-subtitle">
                        Your lost item matches an item that was already reported as found.
                    </div>
                    <div class="alert alert-success">
                        🔔 A notification has been sent to <b>{{ name }}</b>.
                    </div>
                    <p class="section-copy">
                        📱 Open Notifications to see the finder's contact number.
                    </p>
                    <a class="btn btn-primary" href="/">🏠 Back to Home</a>
                    <a class="btn btn-soft" href="/notifications">🔔 Open Notifications</a>
                </div>
            """, title="Match Found", name=name)

        return styled_page("""
            <div class="result-card">
                <div class="page-title">✅ Lost Item Reported!</div>
                <div class="page-subtitle">Your report has been saved to the system.</div>
                <div class="alert alert-info">
                    <b>Item:</b> {{ item }}<br>
                    <b>Name:</b> {{ name }}
                </div>
                <p class="section-copy">
                    We will notify you automatically if a matching found item is reported.
                </p>
                <a class="btn btn-primary" href="/">🏠 Back to Home</a>
            </div>
        """, title="Lost Item Reported", name=name, item=item)

    return styled_page("""
        <div class="form-card">
            <div class="page-title">Report Lost Item 🔴</div>
            <div class="page-subtitle">
                Add the item details so the owner can be notified when a match is found.
            </div>

            <form method="POST">
                <label>Your Name</label>
                <input type="text" name="name" placeholder="Your name" required>

                <label>Item Name</label>
                <input type="text" name="item" placeholder="e.g. Wallet, ID Card, Phone" required>

                <label>Lost Location</label>
                <input type="text" name="location" placeholder="e.g. Library, Lab 2" required>

                <label>Contact Number</label>
                <input type="tel" name="contact" placeholder="Your contact number" required>

                <button class="btn btn-danger" type="submit">📤 Submit Lost Report</button>
            </form>

            <a class="back" href="/">← Back to Home</a>
        </div>
    """, title="Report Lost Item")


# ============================================================
# REPORT FOUND
# ============================================================

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

        db_execute(
            conn,
            """
            INSERT INTO found_items
            (finder, item, location, contact, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (finder, item, location, contact, session["user_id"])
        )

        all_lost_items = db_execute(
            conn,
            """
            SELECT *
            FROM lost_items
            """
        ).fetchall()

        lost_items = [
            lost for lost in all_lost_items
            if items_match(item, lost["item"])
        ]

        matched_names = []

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
                    (lost["name"], message, lost["user_id"])
                )

            matched_names.append(lost["name"])

        conn.commit()
        conn.close()

        if matched_names:
            names = ", ".join(dict.fromkeys(matched_names))
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">🎉 Match Found!</div>
                    <div class="page-subtitle">
                        The found item matches a lost-item report.
                    </div>
                    <div class="alert alert-success">
                        🔔 Notification sent to: <b>{{ names }}</b>
                    </div>
                    <p class="section-copy">
                        📱 The matched user can see your contact number in their notification.
                    </p>
                    <a class="btn btn-success" href="/">🏠 Back to Home</a>
                </div>
            """, title="Match Found", names=names)

        return styled_page("""
            <div class="result-card">
                <div class="page-title">ℹ️ No Match Found</div>
                <div class="page-subtitle">
                    The found item has been saved successfully.
                </div>
                <div class="alert alert-info">
                    We will keep it in the system for future matching.
                </div>
                <a class="btn btn-primary" href="/">🏠 Back to Home</a>
            </div>
        """, title="No Match Found")

    return styled_page("""
        <div class="form-card">
            <div class="page-title">Report Found Item 🟢</div>
            <div class="page-subtitle">
                Add the details of the item you found so the owner can be notified.
            </div>

            <form method="POST">
                <label>Your Name</label>
                <input type="text" name="finder" placeholder="Your name" required>

                <label>Found Item Name</label>
                <input type="text" name="item" placeholder="e.g. Wallet, Laptop, ID Card" required>

                <label>Found Location</label>
                <input type="text" name="location" placeholder="e.g. Library, Canteen" required>

                <label>Contact Number</label>
                <input type="tel" name="contact" placeholder="Your contact number" required>

                <button class="btn btn-success" type="submit">📤 Submit Found Report</button>
            </form>

            <a class="back" href="/">← Back to Home</a>
        </div>
    """, title="Report Found Item")


# ============================================================
# NOTIFICATIONS
# ============================================================

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

    return styled_page("""
        <div class="info-card">
            <div class="page-title">Notifications 🔔</div>
            <div class="page-subtitle">
                Updates and item matches for <b>{{ name }}</b>.
            </div>

            {% if messages %}
                {% for message in messages %}
                    <div class="item">
                        <div class="item-title">🔔 Update</div>
                        <div class="meta">{{ message["message"] }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="alert alert-info">
                    No notifications found for <b>{{ name }}</b>.
                </div>
            {% endif %}

            <a class="btn btn-primary" href="/">🏠 Back to Home</a>
        </div>
    """, title="Notifications", messages=messages, name=name)


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    search = request.args.get("search", "").strip().lower()
    item_type = request.args.get("type", "all")
    location = request.args.get("location", "").strip().lower()

    conn = get_db()

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

    return styled_page("""
        <div class="info-card">
            <div class="page-title">Your Dashboard 📊</div>
            <div class="page-subtitle">
                Track your own lost and found reports.
            </div>

            <div class="stat-grid">
                <div class="stat">
                    <small>🔴 Lost Items</small>
                    <strong>{{ lost_items|length }}</strong>
                </div>
                <div class="stat">
                    <small>🟢 Found Items</small>
                    <strong>{{ found_items|length }}</strong>
                </div>
            </div>

            <form method="GET" action="/dashboard">
                <label>Search</label>
                <input
                    type="text"
                    name="search"
                    placeholder="🔍 Item, name or location"
                    value="{{ search }}"
                >

                <label>Location</label>
                <input
                    type="text"
                    name="location"
                    placeholder="📍 Filter by location"
                    value="{{ location }}"
                >

                <label>Item Type</label>
                <select name="type">
                    <option value="all" {% if item_type == "all" %}selected{% endif %}>All Items</option>
                    <option value="lost" {% if item_type == "lost" %}selected{% endif %}>🔴 Lost Items</option>
                    <option value="found" {% if item_type == "found" %}selected{% endif %}>🟢 Found Items</option>
                </select>

                <button class="btn btn-primary" type="submit">🔍 Search Reports</button>
            </form>
        </div>

        <div class="info-card" style="margin-top:16px">
            <div class="section-title">🔴 Lost Items</div>

            {% if lost_items %}
                {% for item in lost_items %}
                    <div class="item lost">
                        <div class="item-title">{{ item["item"] }}</div>
                        <div class="meta">👤 {{ item["name"] }} · 📍 {{ item["location"] }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="alert alert-info">No lost items found.</div>
            {% endif %}
        </div>

        <div class="info-card" style="margin-top:16px">
            <div class="section-title">🟢 Found Items</div>

            {% if found_items %}
                {% for item in found_items %}
                    <div class="item found">
                        <div class="item-title">{{ item["item"] }}</div>
                        <div class="meta">👤 Found by {{ item["finder"] }} · 📍 {{ item["location"] }}</div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="alert alert-info">No found items found.</div>
            {% endif %}
        </div>

        <a class="btn btn-soft" href="/">🏠 Back to Home</a>
        <a class="btn btn-danger" href="/logout">🚪 Logout</a>
    """,
    title="Dashboard",
    lost_items=lost_items,
    found_items=found_items,
    search=search,
    location=location,
    item_type=item_type
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ============================================================
# START
# ============================================================

init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
