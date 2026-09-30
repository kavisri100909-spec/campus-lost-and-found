from flask import Flask, request, render_template, render_template_string, session, redirect
from werkzeug.utils import secure_filename
import os
import re
import sqlite3
from datetime import timedelta
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "campus_lost_found_secret_key")
# Keep the login session active even after the browser is closed.
app.permanent_session_lifetime = timedelta(days=30)

# Render provides DATABASE_URL in production.
# Locally, SQLite is used automatically.
DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_DATABASE = "campus.db"
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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


def save_optional_photo(file):
    if not file or not file.filename:
        return None
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return None
    unique_name = f"{session.get('user_id', 'user')}_{__import__('time').time_ns()}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(path)
    return path.replace(os.sep, "/")


def required_form_error(*fields):
    return any(not str(value or "").strip() for value in fields)

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
                description TEXT NOT NULL,
                photo TEXT,
                user_id INTEGER,
                matched INTEGER DEFAULT 0
            )
        """)

        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS found_items (
                id SERIAL PRIMARY KEY,
                finder TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                description TEXT NOT NULL,
                photo TEXT,
                user_id INTEGER,
                matched INTEGER DEFAULT 0
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
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS notification_type TEXT DEFAULT 'info'
        """)
        conn.cursor().execute("""
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS reference_id INTEGER
        """)
        conn.cursor().execute("""
            CREATE TABLE IF NOT EXISTS match_requests (
                id SERIAL PRIMARY KEY,
                lost_id INTEGER NOT NULL,
                found_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        conn.cursor().execute("""
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS notification_type TEXT DEFAULT 'info'
        """)
        conn.cursor().execute("""
            ALTER TABLE notifications
            ADD COLUMN IF NOT EXISTS reference_id INTEGER
        """)
        conn.cursor().execute("""
            ALTER TABLE lost_items
            ADD COLUMN IF NOT EXISTS matched INTEGER DEFAULT 0
        """)
        conn.cursor().execute("""
            ALTER TABLE found_items
            ADD COLUMN IF NOT EXISTS matched INTEGER DEFAULT 0
        """)
        conn.cursor().execute("""
            ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''
        """)
        conn.cursor().execute("""
            ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS photo TEXT
        """)
        conn.cursor().execute("""
            ALTER TABLE found_items ADD COLUMN IF NOT EXISTS description TEXT DEFAULT ''
        """)
        conn.cursor().execute("""
            ALTER TABLE found_items ADD COLUMN IF NOT EXISTS photo TEXT
        """)

    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lost_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                description TEXT NOT NULL,
                photo TEXT,
                user_id INTEGER,
                matched INTEGER DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS found_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finder TEXT NOT NULL,
                item TEXT NOT NULL,
                location TEXT NOT NULL,
                contact TEXT NOT NULL,
                description TEXT NOT NULL,
                photo TEXT,
                user_id INTEGER,
                matched INTEGER DEFAULT 0
            )
        """)

        # Create notifications before checking/updating its columns.
        # This is required for a fresh SQLite database on Render/local runs.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER
            )
        """)

        notification_columns = [row["name"] for row in conn.execute("PRAGMA table_info(notifications)").fetchall()]
        if "notification_type" not in notification_columns:
            conn.execute("ALTER TABLE notifications ADD COLUMN notification_type TEXT DEFAULT 'info'")
        if "reference_id" not in notification_columns:
            conn.execute("ALTER TABLE notifications ADD COLUMN reference_id INTEGER")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS match_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lost_id INTEGER NOT NULL,
                found_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
            "notifications": "user_id",
            "lost_items_matched": "matched",
            "found_items_matched": "matched",
            "lost_items_description": "description",
            "lost_items_photo": "photo",
            "found_items_description": "description",
            "found_items_photo": "photo"
        }

        for table, column in tables.items():
            actual_table = table
            if table == "lost_items_matched": actual_table, column = "lost_items", "matched"
            elif table == "found_items_matched": actual_table, column = "found_items", "matched"
            elif table == "lost_items_description": actual_table, column = "lost_items", "description"
            elif table == "lost_items_photo": actual_table, column = "lost_items", "photo"
            elif table == "found_items_description": actual_table, column = "found_items", "description"
            elif table == "found_items_photo": actual_table, column = "found_items", "photo"
            columns = conn.execute(f"PRAGMA table_info({actual_table})").fetchall()
            column_names = [row["name"] for row in columns]
            if column not in column_names:
                conn.execute(f"ALTER TABLE {actual_table} ADD COLUMN {column} INTEGER DEFAULT 0")

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
            session.permanent = True
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
                <input type="text" name="username" placeholder="Enter your username" autocomplete="username" required>

                <label>Password</label>
                <input type="password" name="password" placeholder="Enter your password" autocomplete="current-password" required>

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
                <input type="text" name="username" placeholder="Choose a username" autocomplete="username" required>

                <label>Password</label>
                <input type="password" name="password" placeholder="Create a password" autocomplete="new-password" required>

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
        name = request.form.get("name", "").strip()
        item = request.form.get("item", "").strip().lower()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()
        description = request.form.get("description", "").strip()
        photo = save_optional_photo(request.files.get("photo"))

        if required_form_error(name, item, location, contact, description):
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">⚠️ Missing Details</div>
                    <div class="alert alert-info">Name, item, location and contact number are compulsory.</div>
                    <a class="btn btn-primary" href="/report-lost">← Go Back</a>
                </div>
            """, title="Missing Details")

        conn = get_db()

        lost_insert = db_execute(
            conn,
            """
            INSERT INTO lost_items
            (name, item, location, contact, description, photo, user_id, matched)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            RETURNING id
            """,
            (name, item, location, contact, description, photo, session["user_id"])
        )
        lost_row = lost_insert.fetchone()
        lost_id = lost_row["id"] if isinstance(lost_row, dict) else lost_row[0]

        all_found_items = db_execute(
            conn,
            "SELECT * FROM found_items WHERE COALESCE(matched, 0) = 0"
        ).fetchall()

        found_items = [
            found for found in all_found_items
            if items_match(item, found["item"])
        ]

        pending_created = False
        for found in found_items:
            existing = db_execute(
                conn,
                """
                SELECT id FROM match_requests
                WHERE lost_id = ? AND found_id = ? AND status = 'pending'
                LIMIT 1
                """,
                (lost_id, found["id"])
            ).fetchone()

            if existing:
                continue

            request_insert = db_execute(
                conn,
                """
                INSERT INTO match_requests (lost_id, found_id, status)
                VALUES (?, ?, 'pending')
                RETURNING id
                """,
                (lost_id, found["id"])
            )
            request_row = request_insert.fetchone()
            match_id = request_row["id"] if isinstance(request_row, dict) else request_row[0]

            message = (
                f"🔎 Possible match for '{found['item']}'. "
                f"Lost person says: {description} "
                f"Please check the item you found and choose Yes, I Found This or Not My Item."
            )
            db_execute(
                conn,
                """
                INSERT INTO notifications
                (name, message, user_id, notification_type, reference_id)
                VALUES (?, ?, ?, 'match_request', ?)
                """,
                (found["finder"], message, found["user_id"], match_id)
            )
            pending_created = True

        conn.commit()
        conn.close()

        if pending_created:
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">🔎 Possible Match Found</div>
                    <div class="page-subtitle">
                        A possible match was sent to the person who reported the found item.
                    </div>
                    <div class="alert alert-info">
                        They must check your identifying description and confirm the match first.
                    </div>
                    <a class="btn btn-primary" href="/">🏠 Back to Home</a>
                </div>
            """, title="Possible Match", name=name)

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

            <form method="POST" enctype="multipart/form-data">
                <label>Your Name</label>
                <input type="text" name="name" placeholder="Your name" required>

                <label>Item Name</label>
                <input type="text" name="item" placeholder="e.g. Wallet, ID Card, Phone" required>

                <label>Lost Location</label>
                <input type="text" name="location" placeholder="e.g. Library, Lab 2" required>

                <label>Contact Number</label>
                <input type="tel" name="contact" placeholder="Your contact number" required>

                <label>Item Description / Identifying Details</label>
                <textarea name="description" placeholder="Describe unique details of the item" required></textarea>

                <label>Item Photo (Optional)</label>
                <input type="file" name="photo" accept="image/png,image/jpeg,image/webp">

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
        finder = request.form.get("finder", "").strip()
        item = request.form.get("item", "").strip()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()

        if required_form_error(finder, item, location, contact):
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">⚠️ Missing Details</div>
                    <div class="alert alert-info">Name, item, location, contact number and description are compulsory. Photo is optional.</div>
                    <a class="btn btn-primary" href="/report-found">← Go Back</a>
                </div>
            """, title="Missing Details")

        conn = get_db()

        found_insert = db_execute(
            conn,
            """
            INSERT INTO found_items
            (finder, item, location, contact, description, photo, user_id, matched)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            RETURNING id
            """,
            (finder, item, location, contact, "", None, session["user_id"])
        )
        found_row = found_insert.fetchone()
        found_id = found_row["id"] if isinstance(found_row, dict) else found_row[0]

        all_lost_items = db_execute(
            conn,
            """
            SELECT * FROM lost_items
            WHERE COALESCE(matched, 0) = 0
            """
        ).fetchall()

        lost_items = [
            lost for lost in all_lost_items
            if items_match(item, lost["item"])
        ]

        pending_created = False
        for lost in lost_items:
            existing = db_execute(
                conn,
                """
                SELECT id FROM match_requests
                WHERE lost_id = ? AND found_id = ? AND status = 'pending'
                LIMIT 1
                """,
                (lost["id"], found_id)
            ).fetchone()

            if existing:
                continue

            request_insert = db_execute(
                conn,
                """
                INSERT INTO match_requests (lost_id, found_id, status)
                VALUES (?, ?, 'pending')
                RETURNING id
                """,
                (lost["id"], found_id)
            )
            request_row = request_insert.fetchone()
            match_id = request_row["id"] if isinstance(request_row, dict) else request_row[0]

            message = (
                f"🔎 Possible match for '{item}'. "
                f"The lost person says: {lost['description']} "
                f"Please check your found item and choose Yes, I Found This or Not My Item."
            )
            db_execute(
                conn,
                """
                INSERT INTO notifications
                (name, message, user_id, notification_type, reference_id)
                VALUES (?, ?, ?, 'match_request', ?)
                """,
                (finder, message, session["user_id"], match_id)
            )
            pending_created = True

        conn.commit()
        conn.close()

        if pending_created:
            return styled_page("""
                <div class="result-card">
                    <div class="page-title">🔎 Possible Match Found</div>
                    <div class="page-subtitle">
                        A possible match was found. The lost-item owner will only be contacted after you confirm it.
                    </div>
                    <div class="alert alert-info">
                        Open Notifications and check the identifying description before accepting.
                    </div>
                    <a class="btn btn-primary" href="/notifications">🔔 Open Notifications</a>
                    <a class="btn btn-soft" href="/">🏠 Back to Home</a>
                </div>
            """, title="Possible Match")

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

                <div class="alert alert-info" style="margin-top:16px;">
                    ℹ️ For a found report, only the item name, location and contact details are required.
                </div>

                <button class="btn btn-success" type="submit">📤 Submit Found Report</button>
            </form>

            <a class="back" href="/">← Back to Home</a>
        </div>
    """, title="Report Found Item")


# ============================================================
# MATCH CONFIRMATION
# ============================================================

@app.route("/confirm-match/<int:match_id>", methods=["POST"])
def confirm_match(match_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    match = db_execute(
        conn,
        "SELECT * FROM match_requests WHERE id = ? AND status = 'pending'",
        (match_id,)
    ).fetchone()

    if not match:
        conn.close()
        return redirect("/notifications")

    found = db_execute(
        conn,
        "SELECT * FROM found_items WHERE id = ?",
        (match["found_id"],)
    ).fetchone()
    lost = db_execute(
        conn,
        "SELECT * FROM lost_items WHERE id = ?",
        (match["lost_id"],)
    ).fetchone()

    if not found or not lost or found["user_id"] != session["user_id"]:
        conn.close()
        return redirect("/notifications")

    db_execute(conn, "UPDATE match_requests SET status = 'confirmed' WHERE id = ?", (match_id,))
    db_execute(conn, "UPDATE lost_items SET matched = 1 WHERE id = ?", (lost["id"],))
    db_execute(conn, "UPDATE found_items SET matched = 1 WHERE id = ?", (found["id"],))

    # Close every other pending request involving either item.
    db_execute(
        conn,
        """
        UPDATE match_requests
        SET status = 'closed'
        WHERE status = 'pending'
          AND id <> ?
          AND (lost_id = ? OR found_id = ?)
        """,
        (match_id, lost["id"], found["id"])
    )

    # Tell the lost-item owner only after the finder confirms.
    message = (
        f"✅ Match confirmed for '{lost['item']}'. "
        f"Found by {found['finder']}. Found at {found['location']}. "
        f"📞 Contact: {found['contact']}"
    )
    db_execute(
        conn,
        """
        INSERT INTO notifications
        (name, message, user_id, notification_type, reference_id)
        VALUES (?, ?, ?, 'match_confirmed', ?)
        """,
        (lost["name"], message, lost["user_id"], None)
    )

    db_execute(
        conn,
        """
        INSERT INTO notifications
        (name, message, user_id, notification_type, reference_id)
        VALUES (?, ?, ?, 'info', NULL)
        """,
        (found["finder"], f"✅ You confirmed the match for '{found['item']}'. The owner has been notified.", found["user_id"])
    )

    conn.commit()
    conn.close()
    return redirect("/notifications")


@app.route("/reject-match/<int:match_id>", methods=["POST"])
def reject_match(match_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    match = db_execute(
        conn,
        "SELECT * FROM match_requests WHERE id = ? AND status = 'pending'",
        (match_id,)
    ).fetchone()

    if match:
        found = db_execute(
            conn,
            "SELECT * FROM found_items WHERE id = ?",
            (match["found_id"],)
        ).fetchone()
        if found and found["user_id"] == session["user_id"]:
            db_execute(conn, "UPDATE match_requests SET status = 'rejected' WHERE id = ?", (match_id,))
            db_execute(conn, "DELETE FROM notifications WHERE user_id = ? AND notification_type = 'match_request' AND reference_id = ?", (session["user_id"], match_id))
            conn.commit()

    conn.close()
    return redirect("/notifications")


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route("/delete-notification/<int:notification_id>", methods=["POST"])
def delete_notification(notification_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    db_execute(
        conn,
        "DELETE FROM notifications WHERE id = ? AND user_id = ?",
        (notification_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect("/notifications")


@app.route("/notifications")
def show_notifications():
    if "user_id" not in session:
        return redirect("/login")

    name = session["username"]
    conn = get_db()
    messages = db_execute(
        conn,
        """
        SELECT id, message, notification_type, reference_id
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
                Updates and possible matches for <b>{{ name }}</b>.
            </div>

            {% if messages %}
                {% for message in messages %}
                    <div class="item">
                        <div class="item-title">
                            {% if message["notification_type"] == "match_request" %}
                                🔎 Possible Match
                            {% elif message["notification_type"] == "match_confirmed" %}
                                ✅ Match Confirmed
                            {% else %}
                                🔔 Update
                            {% endif %}
                        </div>
                        <div class="meta">{{ message["message"] }}</div>

                        {% if message["notification_type"] == "match_request" %}
                            <form method="POST" action="/confirm-match/{{ message["reference_id"] }}">
                                <button class="btn btn-success" type="submit">✅ Yes, I Found This</button>
                            </form>
                            <form method="POST" action="/reject-match/{{ message["reference_id"] }}">
                                <button class="btn btn-danger" type="submit">❌ Not My Item</button>
                            </form>
                        {% endif %}

                        <form method="POST" action="/delete-notification/{{ message["id"] }}" style="margin-top:10px;">
                            <button class="btn btn-soft" type="submit" style="width:auto; padding:8px 14px;">🗑️ Delete</button>
                        </form>
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
                Track your own lost and found reports. You can delete your own reports anytime.
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
                        <form method="POST" action="/delete-report/lost/{{ item["id"] }}" onsubmit="return confirm('Delete this lost report?');">
                            <button class="btn btn-danger" type="submit" style="width:auto;padding:9px 14px;margin-top:10px;">🗑️ Delete Report</button>
                        </form>
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
                        <form method="POST" action="/delete-report/found/{{ item["id"] }}" onsubmit="return confirm('Delete this found report?');">
                            <button class="btn btn-danger" type="submit" style="width:auto;padding:9px 14px;margin-top:10px;">🗑️ Delete Report</button>
                        </form>
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
# DELETE REPORT
# ============================================================

@app.route("/delete-report/<item_type>/<int:item_id>", methods=["POST"])
def delete_report(item_type, item_id):
    if "user_id" not in session:
        return redirect("/login")

    if item_type not in ("lost", "found"):
        return redirect("/dashboard")

    table = "lost_items" if item_type == "lost" else "found_items"

    conn = get_db()

    # Only the person who created the report can delete it.
    owner = db_execute(
        conn,
        f"SELECT user_id FROM {table} WHERE id = ?",
        (item_id,)
    ).fetchone()

    if not owner or owner["user_id"] != session["user_id"]:
        conn.close()
        return redirect("/dashboard")

    # Close pending match requests connected to this report.
    if item_type == "lost":
        db_execute(
            conn,
            "UPDATE match_requests SET status = 'closed' WHERE lost_id = ? AND status = 'pending'",
            (item_id,)
        )
    else:
        db_execute(
            conn,
            "UPDATE match_requests SET status = 'closed' WHERE found_id = ? AND status = 'pending'",
            (item_id,)
        )

    db_execute(conn, f"DELETE FROM {table} WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    return redirect("/dashboard")

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
    
