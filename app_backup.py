from flask import Flask, request, render_template_string

app = Flask(__name__)

# Store lost items
lost_items = []

# Store notifications for users
notifications = {}


# ---------------- HOME PAGE ----------------
HOME = """
<!DOCTYPE html>
<html>
<head>
    <title>Campus Lost & Found</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #eef6ff;
            margin: 0;
            padding: 0;
        }

        .header {
            background: #1769aa;
            color: white;
            padding: 30px;
            text-align: center;
        }

        .container {
            width: 80%;
            max-width: 800px;
            margin: 35px auto;
        }

        .card {
            background: white;
            padding: 25px;
            margin-bottom: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }

        h1 {
            margin: 0;
            font-size: 35px;
        }

        h2 {
            color: #1769aa;
        }

        p {
            font-size: 17px;
        }

        .button {
            display: inline-block;
            background: #1769aa;
            color: white;
            padding: 12px 20px;
            margin: 8px;
            border-radius: 8px;
            text-decoration: none;
        }

        .button:hover {
            background: #0d4f82;
        }

        input {
            padding: 12px;
            width: 60%;
            border: 1px solid #bbb;
            border-radius: 7px;
        }

        button {
            padding: 12px 18px;
            background: #1769aa;
            color: white;
            border: none;
            border-radius: 7px;
            cursor: pointer;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
    </style>
</head>

<body>

    <div class="header">
        <h1>🎓 Campus Lost & Found</h1>
        <p>Lost it? Report it. Found it? Return it.</p>
    </div>

    <div class="container">

        <div class="card">
            <h2>🔍 Lost Something?</h2>
            <p>
                Report your lost item and get notified when someone finds it.
            </p>

            <a class="button" href="/report-lost">
                🔴 Report Lost Item
            </a>

            <a class="button" href="/report-found">
                🟢 Report Found Item
            </a>
        </div>

        <div class="card">
            <h2>🔔 Check Notifications</h2>

            <p>
                Enter your name to check whether your lost item has been found.
            </p>

            <form action="/notifications" method="get">
                <input
                    type="text"
                    name="name"
                    placeholder="Enter your name"
                    required
                >

                <button type="submit">
                    Check Notifications
                </button>
            </form>
        </div>

        <div class="card">
            <h2>🤝 How It Works</h2>

            <p>1️⃣ Report your lost item.</p>
            <p>2️⃣ Someone finds the item and reports it.</p>
            <p>3️⃣ The system automatically checks for a match.</p>
            <p>4️⃣ The owner receives a notification.</p>
        </div>

    </div>

    <div class="footer">
        <p>© 2026 Campus Lost & Found</p>
    </div>

</body>
</html>
"""


# ---------------- HOME ROUTE ----------------
@app.route("/")
def home():
    return render_template_string(HOME)


# ---------------- REPORT LOST ITEM ----------------
@app.route("/report-lost", methods=["GET", "POST"])
def report_lost():

    if request.method == "POST":

        name = request.form["name"]
        item = request.form["item"]
        location = request.form["location"]

        lost_items.append({
            "name": name,
            "item": item.lower(),
            "location": location
        })

        return render_template_string("""
        <h1>✅ Lost Item Reported!</h1>

        <p><b>Name:</b> {{ name }}</p>
        <p><b>Item:</b> {{ item }}</p>
        <p><b>Location:</b> {{ location }}</p>

        <p>Your item has been added to the system.</p>

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


# ---------------- REPORT FOUND ITEM ----------------
@app.route("/report-found", methods=["GET", "POST"])
def report_found():

    if request.method == "POST":

        finder = request.form["finder"]
        item = request.form["item"].lower()
        location = request.form["location"]

        # Check whether item matches a lost item
        matches = []

        for lost in lost_items:

            if lost["item"] == item:

                matches.append(lost)

                # Create notification for owner
                message = (
                    f"🔔 Your lost item '{item}' has been found! "
                    f"It was found at {location}. "
                    f"Found by {finder}."
                )

                if lost["name"] not in notifications:
                    notifications[lost["name"]] = []

                notifications[lost["name"]].append(message)

        if matches:

            names = ", ".join([m["name"] for m in matches])

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

            <p>No matching lost-item report was found.</p>

            <p>The found item has not been matched yet.</p>

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

    name = request.args.get("name", "")

    user_notifications = notifications.get(name, [])

    return render_template_string("""
    <h1>🔔 Your Notifications</h1>

    {% if messages %}

        {% for message in messages %}
            <p>🟢 {{ message }}</p>
        {% endfor %}

    {% else %}

        <p>No notifications found for <b>{{ name }}</b>.</p>

    {% endif %}

    <br>
    <a href="/">← Back to Home</a>
    """,
    name=name,
    messages=user_notifications)


# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)