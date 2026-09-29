import os
import random
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, UnidentifiedImageError

from config import ALLOWED_EXTENSIONS, DATABASE, DEBUG, SECRET_KEY, UPLOAD_FOLDER

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["DATABASE"] = DATABASE
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.jinja_env.globals["csrf_token"] = lambda: session.get("csrf_token") or session.__setitem__("csrf_token", secrets.token_hex(16))

BIRTHDAYS = [
    {
        "id": "asmita",
        "name": "Ashmita",
        "birth_year": 2006,
        "birth_month": 9,
        "birth_day": 30,
        "partner_name": "Raj",
        "avatar": "👸",
        "title": "Birthday Queen",
        "wishes": "Happy Birthday to the most gorgeous, sweet, and caring soul! You make every single day feel magical and special! 🎂💖✨",
    },
    {
        "id": "raj",
        "name": "Raj",
        "birth_year": 2003,
        "birth_month": 7,
        "birth_day": 7,
        "partner_name": "Ashmita",
        "avatar": "🤴",
        "title": "Birthday King",
        "wishes": "Happy Birthday to my favourite person in the whole universe! Thank you for filling life with laughter and love! 🎂💖✨",
    },
]

ROMANTIC_HINDI_SONGS = [
    {
        "id": "LUgpPmj6nR8",
        "title": "Khat",
        "movie": "Single",
        "artist": "Navjot Ahuja",
    },
    {
        "id": "mt9xg0mmt28",
        "title": "Tum Se Hi",
        "movie": "Jab We Met",
        "artist": "Mohit Chauhan",
    },
    {
        "id": "BddP6PYo2gs",
        "title": "Kesariya",
        "movie": "Brahmāstra",
        "artist": "Arijit Singh",
    },
    {
        "id": "gvyUuxdRdR4",
        "title": "Raataan Lambiyan",
        "movie": "Shershaah",
        "artist": "Jubin Nautiyal & Asees Kaur",
    },
    {
        "id": "ElZfdU54Cp8",
        "title": "Apna Bana Le",
        "movie": "Bhediya",
        "artist": "Arijit Singh",
    },
    {
        "id": "pElk1ShPrcE",
        "title": "Pehla Nasha",
        "movie": "Jo Jeeta Wohi Sikandar",
        "artist": "Udit Narayan & Sadhana Sargam",
    },
    {
        "id": "3X81L48qYv0",
        "title": "Tera Ban Jaunga",
        "movie": "Kabir Singh",
        "artist": "Akhil Sachdeva & Tulsi Kumar",
    },
    {
        "id": "Z9AZkZ5Zq2U",
        "title": "Janam Janam",
        "movie": "Dilwale",
        "artist": "Arijit Singh & Antara Mitra",
    },
    {
        "id": "cYOB941gyXI",
        "title": "Hawayein",
        "movie": "Jab Harry Met Sejal",
        "artist": "Arijit Singh",
    },
    {
        "id": "IJq0cmW6DVo",
        "title": "Tum Hi Ho",
        "movie": "Aashiqui 2",
        "artist": "Arijit Singh",
    },
    {
        "id": "2mxeYgJ_u4E",
        "title": "Subhanallah",
        "movie": "Yeh Jawaani Hai Deewani",
        "artist": "Sreerama Chandra",
    },
]


def get_ordinal_suffix(n):
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def get_birthday_celebration():
    today = datetime.now()

    # Allow testing via ?test_bday=asmita or ?test_bday=raj, or clear with ?test_bday=off
    if request:
        test_arg = request.args.get("test_bday")
        if test_arg is not None:
            val = test_arg.strip().lower()
            if val in ("asmita", "raj"):
                session["test_bday"] = val
            elif val in ("off", "none", "clear", "0"):
                session.pop("test_bday", None)

    active_test = session.get("test_bday") if session else None

    for person in BIRTHDAYS:
        is_actual_birthday = (today.month == person["birth_month"] and today.day == person["birth_day"])
        is_test = (active_test == person["id"])

        if is_actual_birthday or is_test:
            age = today.year - person["birth_year"]
            return {
                "is_birthday": True,
                "id": person["id"],
                "name": person["name"],
                "age": age,
                "age_formatted": get_ordinal_suffix(age),
                "partner_name": person["partner_name"],
                "avatar": person["avatar"],
                "title": person["title"],
                "wishes": person["wishes"],
                "is_test_mode": is_test and not is_actual_birthday,
            }
    return None


@app.context_processor
def inject_global_data():
    bday = get_birthday_celebration()
    user_id = session.get("user_id")
    current_user = get_user_by_id(user_id) if user_id else None
    partner = get_user_by_id(partner_id(user_id)) if user_id else None
    return {
        "birthday_info": bday,
        "birthday_songs": ROMANTIC_HINDI_SONGS,
        "initial_birthday_song": ROMANTIC_HINDI_SONGS[0],
        "current_user": current_user,
        "current_partner": partner,
        "current_year": datetime.now().year,
    }



@app.route("/api/birthday-songs")
def api_birthday_songs():
    return jsonify({
        "songs": ROMANTIC_HINDI_SONGS,
        "random_song": random.choice(ROMANTIC_HINDI_SONGS),
    })


def get_db():
    connection = sqlite3.connect(app.config["DATABASE"])
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db()
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            caption TEXT,
            uploaded_by INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uploaded_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS music_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            song_title TEXT NOT NULL,
            youtube_url TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS food_wishes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_name TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS partner_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS live_locations (
            user_id INTEGER PRIMARY KEY,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """
    )
    connection.commit()
    connection.close()


def ensure_default_users():
    connection = get_db()
    default_users = [
        ("Raj", "raj", "DEFAULT_RAJ_PASSWORD", os.getenv("DEFAULT_RAJ_PASSWORD")),
        ("Ashmita", "asmita", "DEFAULT_ASMITA_PASSWORD", os.getenv("DEFAULT_ASMITA_PASSWORD")),
    ]

    for name, username, password_variable, password in default_users:
        if not password or password.startswith("replace-"):
            connection.close()
            raise RuntimeError(f"Set {password_variable} to a unique password in your local .env file.")

        existing = connection.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            connection.execute(
                "UPDATE users SET name = ?, password_hash = ? WHERE username = ?",
                (name, generate_password_hash(password), username),
            )
        else:
            connection.execute(
                "INSERT INTO users (name, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, username, generate_password_hash(password), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
            )

    connection.commit()
    connection.close()


@app.before_request
def setup_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)


@app.before_request
def require_authenticated_user():
    if session.get("user_id") or request.endpoint in {"login", "static"}:
        return None
    return redirect(url_for("login"))


@app.before_request
def protect_routes():
    if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
        if request.path.startswith("/static"):
            return None
        if request.path in {"/login"}:
            return None

        incoming_csrf = (
            request.form.get("_csrf_token")
            or request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
        )
        if not incoming_csrf and request.is_json:
            json_body = request.get_json(silent=True) or {}
            incoming_csrf = json_body.get("_csrf_token")

        if incoming_csrf != session.get("csrf_token"):
            abort(403)



def login_required(view):
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


def get_user_by_username(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user


def partner_id(user_id):
    conn = get_db()
    partner = conn.execute("SELECT id FROM users WHERE id != ? ORDER BY id LIMIT 1", (user_id,)).fetchone()
    conn.close()
    if partner:
        return partner["id"]
    return None


def get_latest_music():
    conn = get_db()
    item = conn.execute(
        "SELECT mh.*, u.name AS user_name FROM music_history mh JOIN users u ON u.id = mh.user_id ORDER BY mh.created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return item


def get_previous_music():
    conn = get_db()
    row = conn.execute(
        "SELECT mh.*, u.name AS user_name FROM music_history mh JOIN users u ON u.id = mh.user_id ORDER BY mh.created_at DESC LIMIT 2"
    ).fetchall()
    conn.close()
    if len(row) > 1:
        return row[1]
    return None


def classify_vibe(song_title):
    text = (song_title or "").lower()
    if any(keyword in text for keyword in ["tum se hi", "love", "romantic", "forever", "you", "heart", "beautiful", "kiss", "humsafar"]):
        return "❤️ Romantic"
    if any(keyword in text for keyword in ["happy", "party", "dance", "sunshine", "smile", "celebrate", "fun", "joy"]):
        return "🎉 Party"
    if any(keyword in text for keyword in ["sad", "melancholy", "cry", "lonely", "blue", "missing", "tears", "rain"]):
        return "😢 Melancholic"
    if any(keyword in text for keyword in ["calm", "slow", "peace", "quiet", "soft", "night", "dream", "cloud"]):
        return "😌 Calm"
    if any(keyword in text for keyword in ["energy", "power", "run", "fire", "anthem", "battle", "rock", "speed"]):
        return "⚡ Energetic"
    if any(keyword in text for keyword in ["nostalgia", "memories", "old", "childhood", "home", "time", "again", "past"]):
        return "🥹 Nostalgic"
    return "😊 Happy"


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        user = get_user_by_username(username)
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_user_by_id(session["user_id"])
    partner = get_user_by_id(partner_id(session["user_id"]))
    conn = get_db()
    photo_count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
    message_count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    food_count = conn.execute("SELECT COUNT(*) FROM food_wishes").fetchone()[0]
    note_count = conn.execute("SELECT COUNT(*) FROM partner_notes").fetchone()[0]
    music_count = conn.execute("SELECT COUNT(*) FROM music_history").fetchone()[0]
    location_count = conn.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
    latest_photo = conn.execute(
        "SELECT p.*, u.name as uploader FROM photos p JOIN users u ON u.id = p.uploaded_by ORDER BY p.created_at DESC LIMIT 1"
    ).fetchone()
    latest_message = conn.execute(
        "SELECT m.*, u.name as sender_name FROM messages m JOIN users u ON u.id = m.sender_id ORDER BY m.created_at DESC LIMIT 1"
    ).fetchone()
    latest_music = conn.execute(
        "SELECT mh.*, u.name as user_name FROM music_history mh JOIN users u ON u.id = mh.user_id ORDER BY mh.created_at DESC LIMIT 1"
    ).fetchone()
    latest_note = conn.execute(
        "SELECT pn.*, u.name as user_name FROM partner_notes pn JOIN users u ON u.id = pn.user_id ORDER BY pn.created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return render_template(
        "dashboard.html",
        user=user,
        partner=partner,
        photo_count=photo_count,
        message_count=message_count,
        food_count=food_count,
        note_count=note_count,
        music_count=music_count,
        location_count=location_count,
        latest_photo=latest_photo,
        latest_message=latest_message,
        latest_music=latest_music,
        latest_note=latest_note,
    )



def save_and_compress_image(file_storage, upload_folder, max_dimension=1600, quality=80):
    upload_path = Path(upload_folder)
    upload_path.mkdir(parents=True, exist_ok=True)

    unique_id = secrets.token_hex(8)
    img = Image.open(file_storage)

    # Preserve animated GIF if applicable
    if getattr(img, "is_animated", False):
        filename = f"{unique_id}.gif"
        target_path = upload_path / filename
        img.save(target_path, save_all=True, optimize=True)
        return filename

    # Auto-orient based on phone EXIF data
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Normalize color modes (keep transparency for RGBA/palette, otherwise RGB)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Downscale while preserving aspect ratio if dimension exceeds max_dimension
    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    # Save as highly compressed WebP
    filename = f"{unique_id}.webp"
    target_path = upload_path / filename
    img.save(target_path, "WEBP", quality=quality, method=6)
    return filename


@app.route("/gallery", methods=["GET", "POST"])
@login_required
def gallery():
    if request.method == "POST":
        file = request.files.get("photo")
        caption = (request.form.get("caption") or "").strip()

        if not file or file.filename == "":
            flash("Please choose a valid photo.", "warning")
            return redirect(url_for("gallery"))

        extension = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            flash("Only JPG, PNG, GIF, and WEBP images are allowed.", "danger")
            return redirect(url_for("gallery"))

        try:
            unique_name = save_and_compress_image(file, app.config["UPLOAD_FOLDER"])
        except (UnidentifiedImageError, OSError):
            flash("The uploaded file is not a valid or readable image.", "danger")
            return redirect(url_for("gallery"))
        except Exception:
            flash("An error occurred while compressing and saving the image.", "danger")
            return redirect(url_for("gallery"))

        conn = get_db()
        conn.execute(
            "INSERT INTO photos (filename, caption, uploaded_by, created_at) VALUES (?, ?, ?, ?)",
            (unique_name, caption or "A treasured memory.", session["user_id"], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        flash("Photo uploaded and optimized successfully.", "success")
        return redirect(url_for("gallery"))

    conn = get_db()
    photos = conn.execute(
        "SELECT p.*, u.name AS uploader, u.username AS uploader_username FROM photos p JOIN users u ON u.id = p.uploaded_by ORDER BY p.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("gallery.html", photos=photos)


@app.route("/gallery/delete/<int:photo_id>", methods=["POST"])
@login_required
def delete_gallery_photo(photo_id):
    conn = get_db()
    photo = conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
    if not photo:
        conn.close()
        flash("Photo not found.", "warning")
        return redirect(url_for("gallery"))

    file_path = Path(app.config["UPLOAD_FOLDER"]) / photo["filename"]
    if file_path.exists():
        file_path.unlink()

    conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
    conn.commit()
    conn.close()
    flash("Photo deleted.", "success")
    return redirect(url_for("gallery"))


@app.route("/messages", methods=["GET", "POST"])
@login_required
def messages():
    current_user = get_user_by_id(session["user_id"])
    partner = get_user_by_id(partner_id(session["user_id"]))

    if request.method == "POST":
        message_text = (request.form.get("message") or "").strip()
        if not message_text:
            flash("Message cannot be empty.", "warning")
            return redirect(url_for("messages"))

        receiver_id = int(request.form.get("receiver_id") or partner_id(session["user_id"]))
        conn = get_db()
        conn.execute(
            "INSERT INTO messages (sender_id, receiver_id, message, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], receiver_id, message_text, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        flash("Your message was sent.", "success")
        return redirect(url_for("messages"))

    conn = get_db()
    message_rows = conn.execute(
        """
        SELECT m.*, s.name AS sender_name, r.name AS receiver_name
        FROM messages m
        JOIN users s ON s.id = m.sender_id
        JOIN users r ON r.id = m.receiver_id
        WHERE m.sender_id IN (?, ?) AND m.receiver_id IN (?, ?)
        ORDER BY m.created_at DESC
        """,
        (session["user_id"], partner["id"], session["user_id"], partner["id"]),
    ).fetchall()
    conn.close()
    return render_template("messages.html", messages=message_rows, current_user=current_user, partner=partner)


@app.route("/messages/delete/<int:message_id>", methods=["POST"])
@login_required
def delete_message(message_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    if not item:
        conn.close()
        flash("Message not found.", "warning")
        return redirect(url_for("messages"))

    if item["sender_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own messages.", "danger")
        return redirect(url_for("messages"))

    conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    flash("Message deleted.", "success")
    return redirect(url_for("messages"))


@app.route("/messages/edit/<int:message_id>", methods=["POST"])
@login_required
def edit_message(message_id):
    new_message = (request.form.get("message") or "").strip()
    if not new_message:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("messages"))

    conn = get_db()
    item = conn.execute("SELECT * FROM messages WHERE id = ?", (message_id,)).fetchone()
    if not item:
        conn.close()
        flash("Message not found.", "warning")
        return redirect(url_for("messages"))

    if item["sender_id"] != session["user_id"]:
        conn.close()
        flash("You can only edit your own messages.", "danger")
        return redirect(url_for("messages"))

    conn.execute(
        "UPDATE messages SET message = ?, updated_at = ? WHERE id = ?",
        (new_message, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), message_id),
    )
    conn.commit()
    conn.close()
    flash("Message updated.", "success")
    return redirect(url_for("messages"))


@app.route("/music", methods=["GET", "POST"])
@login_required
def music():
    if request.method == "POST":
        song_name = (request.form.get("song_title") or "").strip()
        youtube_url = (request.form.get("youtube_url") or "").strip()

        if not song_name and not youtube_url:
            flash("Please enter a song or a YouTube URL.", "warning")
            return redirect(url_for("music"))

        if youtube_url:
            final_url = youtube_url
            title = song_name or "Selected song"
        else:
            title = song_name
            final_url = "https://www.youtube.com/results?search_query=" + quote(song_name)

        conn = get_db()
        conn.execute(
            "INSERT INTO music_history (user_id, song_title, youtube_url, created_at) VALUES (?, ?, ?, ?)",
            (session["user_id"], title, final_url, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        flash("Song saved successfully.", "success")
        return redirect(url_for("music"))

    latest = get_latest_music()
    previous = get_previous_music()
    conn = get_db()
    history = conn.execute(
        "SELECT mh.*, u.name AS user_name FROM music_history mh JOIN users u ON u.id = mh.user_id ORDER BY mh.created_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return render_template("music.html", latest=latest, previous=previous, history=history)


@app.route("/mood")
@login_required
def mood():
    latest = get_latest_music()
    previous = get_previous_music()
    current_vibe = classify_vibe(latest["song_title"]) if latest else "😊 Happy"
    previous_vibe = classify_vibe(previous["song_title"]) if previous else "😊 Happy"
    return render_template("mood.html", latest=latest, previous=previous, current_vibe=current_vibe, previous_vibe=previous_vibe)


@app.route("/food", methods=["GET", "POST"])
@login_required
def food():
    if request.method == "POST":
        food_name = (request.form.get("food_name") or "").strip()
        note = (request.form.get("note") or "").strip()
        if not food_name:
            flash("Food name is required.", "warning")
            return redirect(url_for("food"))

        conn = get_db()
        conn.execute(
            "INSERT INTO food_wishes (user_id, food_name, note, created_at) VALUES (?, ?, ?, ?)",
            (session["user_id"], food_name, note, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        flash("Food wish added.", "success")
        return redirect(url_for("food"))

    conn = get_db()
    food_items = conn.execute(
        "SELECT fw.*, u.name AS user_name FROM food_wishes fw JOIN users u ON u.id = fw.user_id ORDER BY fw.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("food.html", food_items=food_items)


@app.route("/food/delete/<int:food_id>", methods=["POST"])
@login_required
def delete_food(food_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM food_wishes WHERE id = ?", (food_id,)).fetchone()
    if not item:
        conn.close()
        flash("Food wish not found.", "warning")
        return redirect(url_for("food"))

    if item["user_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own food wish.", "danger")
        return redirect(url_for("food"))

    conn.execute("DELETE FROM food_wishes WHERE id = ?", (food_id,))
    conn.commit()
    conn.close()
    flash("Food wish deleted.", "success")
    return redirect(url_for("food"))


@app.route("/food/edit/<int:food_id>", methods=["POST"])
@login_required
def edit_food(food_id):
    food_name = (request.form.get("food_name") or "").strip()
    note = (request.form.get("note") or "").strip()
    if not food_name:
        flash("Food name is required.", "warning")
        return redirect(url_for("food"))

    conn = get_db()
    item = conn.execute("SELECT * FROM food_wishes WHERE id = ?", (food_id,)).fetchone()
    if not item:
        conn.close()
        flash("Food wish not found.", "warning")
        return redirect(url_for("food"))

    if item["user_id"] != session["user_id"]:
        conn.close()
        flash("You can only edit your own food wish.", "danger")
        return redirect(url_for("food"))

    conn.execute(
        "UPDATE food_wishes SET food_name = ?, note = ? WHERE id = ?",
        (food_name, note, food_id),
    )
    conn.commit()
    conn.close()
    flash("Food wish updated.", "success")
    return redirect(url_for("food"))


@app.route("/mood-swings", methods=["GET", "POST"])
@login_required
def mood_swings():
    if request.method == "POST":
        note_text = (request.form.get("note") or "").strip()
        status = request.form.get("status", "pending")
        if not note_text:
            flash("Please write a note.", "warning")
            return redirect(url_for("mood_swings"))

        conn = get_db()
        conn.execute(
            "INSERT INTO partner_notes (user_id, note, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (session["user_id"], note_text, status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )
        conn.commit()
        conn.close()
        flash("Your note is now shared.", "success")
        return redirect(url_for("mood_swings"))

    conn = get_db()
    notes = conn.execute(
        "SELECT pn.*, u.name AS user_name FROM partner_notes pn JOIN users u ON u.id = pn.user_id ORDER BY pn.created_at DESC"
    ).fetchall()
    conn.close()
    return render_template("mood_swings.html", notes=notes)


@app.route("/mood-swings/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM partner_notes WHERE id = ?", (note_id,)).fetchone()
    if not item:
        conn.close()
        flash("Note not found.", "warning")
        return redirect(url_for("mood_swings"))

    if item["user_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own note.", "danger")
        return redirect(url_for("mood_swings"))

    conn.execute("DELETE FROM partner_notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    flash("Note deleted.", "success")
    return redirect(url_for("mood_swings"))


@app.route("/mood-swings/edit/<int:note_id>", methods=["POST"])
@login_required
def edit_note(note_id):
    note_text = (request.form.get("note") or "").strip()
    status = request.form.get("status", "pending")
    if not note_text:
        flash("Note cannot be empty.", "warning")
        return redirect(url_for("mood_swings"))

    conn = get_db()
    item = conn.execute("SELECT * FROM partner_notes WHERE id = ?", (note_id,)).fetchone()
    if not item:
        conn.close()
        flash("Note not found.", "warning")
        return redirect(url_for("mood_swings"))

    if item["user_id"] != session["user_id"]:
        conn.close()
        flash("You can only edit your own note.", "danger")
        return redirect(url_for("mood_swings"))

    conn.execute(
        "UPDATE partner_notes SET note = ?, status = ?, updated_at = ? WHERE id = ?",
        (note_text, status, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), note_id),
    )
    conn.commit()
    conn.close()
    flash("Note updated.", "success")
    return redirect(url_for("mood_swings"))


@app.route("/location", methods=["GET", "POST"])
@login_required
def location():
    conn = get_db()
    recent_locations = conn.execute(
        "SELECT l.*, u.name AS user_name FROM locations l JOIN users u ON u.id = l.user_id ORDER BY l.created_at DESC"
    ).fetchall()
    active_live_locations = conn.execute(
        "SELECT l.*, u.name AS user_name FROM live_locations l JOIN users u ON u.id = l.user_id WHERE l.expires_at > ? ORDER BY l.updated_at DESC",
        (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),),
    ).fetchall()
    conn.close()
    map_location = active_live_locations[0] if active_live_locations else (recent_locations[0] if recent_locations else None)
    return render_template(
        "location.html",
        recent_locations=recent_locations,
        active_live_locations=active_live_locations,
        map_latitude=map_location["latitude"] if map_location else 20.5937,
        map_longitude=map_location["longitude"] if map_location else 78.9629,
    )


@app.route("/location/share", methods=["POST"])
@login_required
def share_location():
    data = request.get_json(silent=True) or request.form
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        if request.is_json:
            return jsonify({"error": "Latitude and longitude are required."}), 400
        flash("Latitude and longitude are required.", "warning")
        return redirect(url_for("location"))

    try:
        lat_value = float(latitude)
        lon_value = float(longitude)
    except (TypeError, ValueError):
        if request.is_json:
            return jsonify({"error": "Invalid location data."}), 400
        flash("Invalid location coordinates.", "danger")
        return redirect(url_for("location"))

    conn = get_db()
    conn.execute(
        "INSERT INTO locations (user_id, latitude, longitude, created_at) VALUES (?, ?, ?, ?)",
        (session["user_id"], lat_value, lon_value, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    if request.is_json:
        return jsonify({"status": "Location shared successfully."})
    flash("Location spot pinned successfully.", "success")
    return redirect(url_for("location"))


@app.route("/api/location/live", methods=["GET", "POST"])
@login_required
def api_live_location():
    conn = get_db()
    now = datetime.utcnow()
    now_text = now.strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "GET":
        locations = conn.execute(
            "SELECT l.user_id, u.name AS user_name, l.latitude, l.longitude, l.started_at, l.updated_at, l.expires_at "
            "FROM live_locations l JOIN users u ON u.id = l.user_id WHERE l.expires_at > ? ORDER BY l.updated_at DESC",
            (now_text,),
        ).fetchall()
        conn.close()
        return jsonify({"locations": [dict(item) for item in locations]})

    data = request.get_json(silent=True) or request.form
    action = (data.get("action") or "").strip().lower()
    user_id = session["user_id"]

    if action == "stop":
        conn.execute("DELETE FROM live_locations WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "stopped"})

    if action not in {"start", "update"}:
        conn.close()
        return jsonify({"error": "Choose start, update, or stop."}), 400

    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
    except (TypeError, ValueError):
        conn.close()
        return jsonify({"error": "Valid latitude and longitude are required."}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        conn.close()
        return jsonify({"error": "Coordinates are outside the valid range."}), 400

    expires_at = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    if action == "start":
        conn.execute(
            "INSERT INTO live_locations (user_id, latitude, longitude, started_at, updated_at, expires_at) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
            "latitude = excluded.latitude, longitude = excluded.longitude, started_at = excluded.started_at, "
            "updated_at = excluded.updated_at, expires_at = excluded.expires_at",
            (user_id, latitude, longitude, now_text, now_text, expires_at),
        )
    else:
        result = conn.execute(
            "UPDATE live_locations SET latitude = ?, longitude = ?, updated_at = ? "
            "WHERE user_id = ? AND expires_at > ?",
            (latitude, longitude, now_text, user_id, now_text),
        )
        if result.rowcount == 0:
            conn.close()
            return jsonify({"error": "Live sharing has ended. Start sharing again."}), 409

    saved_location = conn.execute(
        "SELECT expires_at FROM live_locations WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.commit()
    conn.close()
    return jsonify({"status": "sharing", "expires_at": saved_location["expires_at"]})



@app.route("/location/delete/<int:location_id>", methods=["POST"])
@login_required
def delete_location(location_id):
    conn = get_db()
    item = conn.execute("SELECT * FROM locations WHERE id = ?", (location_id,)).fetchone()
    if not item:
        conn.close()
        flash("Location not found.", "warning")
        return redirect(url_for("location"))

    if item["user_id"] != session["user_id"]:
        conn.close()
        flash("You can only delete your own location records.", "danger")
        return redirect(url_for("location"))

    conn.execute("DELETE FROM locations WHERE id = ?", (location_id,))
    conn.commit()
    conn.close()
    flash("Location history deleted.", "success")
    return redirect(url_for("location"))


@app.route("/uploads/photos/<path:filename>")
@login_required
def uploaded_photo(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


with app.app_context():
    if not os.path.exists(os.path.dirname(DATABASE)):
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db()
    ensure_default_users()


if __name__ == "__main__":
    app.run(debug=DEBUG, host="127.0.0.1", port=5000)
