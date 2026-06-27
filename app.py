from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from googletrans import Translator
from datetime import datetime
import pickle
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# SESSION CONFIG (IMPORTANT)
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'

#  Translator
translator = Translator()

#  Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.secret_key = "supersecretkey"

#  Load ML model
model = pickle.load(open("complaint_model.pkl", "rb"))

#  Create DB
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_text TEXT,
        category TEXT,
        location TEXT,
        image TEXT,
        status TEXT DEFAULT 'Pending',
        submitted_at TEXT,
        resolved_at TEXT
    )
""")
    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route("/")
def home():
    return render_template("index.html")

# ================= PREDICT =================
@app.route("/predict", methods=["POST"])
def predict():
    complaint = request.form["complaint"]
    location = request.form["location"]
    language = request.form["language"]

    submitted_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    #  TRANSLATION
    if language != "en":
        translated = translator.translate(complaint, src=language, dest='en')
        translated_text = translated.text
    else:
        translated_text = complaint

    #  IMAGE UPLOAD
    image_file = request.files.get("image")
    filename = ""

    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image_file.save(image_path)

    #  ML PREDICTION
    prediction = model.predict([translated_text])[0]

    #  SAVE TO DB
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO complaints 
    (complaint_text, category, location, image, status, submitted_at, resolved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    complaint,
    prediction,
    location,
    filename,
    "Pending",
    submitted_time,
    None
))

    conn.commit()
    conn.close()

    return render_template("index.html", result=prediction)

# ================= EMERGENCY =================
@app.route("/emergency", methods=["POST"])
def emergency():
    print("🚨 EMERGENCY ALERT SENT TO ADMIN 🚨")
    return render_template("index.html", result="🚨 Emergency alert sent to admin!")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session.clear()              #  clear old session
            session.permanent = False    #  session ends on browser close
            session["admin"] = True
            return redirect("/admin")
        else:
            return render_template("login.html", error="Invalid Credentials")

    return render_template("login.html")

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    status_filter = request.args.get("status")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if status_filter == "Pending":
        cursor.execute("SELECT * FROM complaints WHERE status='Pending'")

    elif status_filter == "Resolved":
        cursor.execute("SELECT * FROM complaints WHERE status='Resolved'")

    else:
        cursor.execute("SELECT * FROM complaints")

    data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", data=data)
# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Pending'")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status='Resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT category, COUNT(*) FROM complaints GROUP BY category")
    category_data = cursor.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        total=total,
        pending=pending,
        resolved=resolved,
        category_data=category_data
    )

# ================= RESOLVE =================
@app.route("/resolve/<int:id>")
def resolve(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    resolved_time = datetime.now().strftime("%d-%b-%Y %I:%M %p")

    cursor.execute("""
        UPDATE complaints
        SET status='Resolved', resolved_at=?
        WHERE id=?
        """, (resolved_time, id))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= DELETE =================
@app.route("/delete/<int:id>")
def delete(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM complaints WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()   #  remove session completely
    return redirect("/login")


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True, port=5001)