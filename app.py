import os
import random
import secrets
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
    send_file,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, UnidentifiedImageError
from gridfs import GridFSBucket
from pymongo import ASCENDING, DESCENDING, MongoClient, ReturnDocument

from config import ALLOWED_EXTENSIONS, DEBUG, MONGODB_DATABASE, MONGODB_URI, SECRET_KEY, UPLOAD_FOLDER

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.jinja_env.globals["csrf_token"] = lambda: session.get("csrf_token") or session.__setitem__("csrf_token", secrets.token_hex(16))

if not MONGODB_URI:
    raise RuntimeError("Set MONGODB_URI in your local .env file before starting the app.")

try:
    import certifi
    mongo_client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=10000)
except Exception:
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)

mongo_db = mongo_client[MONGODB_DATABASE]
photo_bucket = GridFSBucket(mongo_db, bucket_name="uploads")


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


def init_db():
    mongo_client.admin.command("ping")
    mongo_db.users.create_index([("id", ASCENDING)], unique=True)
    mongo_db.users.create_index([("username", ASCENDING)], unique=True)
    mongo_db.live_locations.create_index([("user_id", ASCENDING)], unique=True)
    mongo_db.live_locations.create_index([("expires_at", ASCENDING)])

    for collection_name in ("photos", "messages", "music_history", "food_wishes", "partner_notes", "locations"):
        mongo_db[collection_name].create_index([("id", ASCENDING)], unique=True)

    for collection_name in ("users", "photos", "messages", "music_history", "food_wishes", "partner_notes", "locations"):
        latest = mongo_db[collection_name].find_one(sort=[("id", DESCENDING)])
        if latest:
            mongo_db.counters.update_one(
                {"_id": collection_name},
                {"$max": {"value": latest["id"]}},
                upsert=True,
            )


def next_id(collection_name):
    counter = mongo_db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return counter["value"]


def document_by_id(collection_name, document_id):
    if document_id is None:
        return None
    try:
        document_id = int(document_id)
    except (TypeError, ValueError):
        return None
    return mongo_db[collection_name].find_one({"id": document_id})


def ensure_default_users():
    default_users = [
        ("Raj", "raj", "DEFAULT_RAJ_PASSWORD", os.getenv("DEFAULT_RAJ_PASSWORD")),
        ("Ashmita", "asmita", "DEFAULT_ASMITA_PASSWORD", os.getenv("DEFAULT_ASMITA_PASSWORD")),
    ]

    for name, username, password_variable, password in default_users:
        if not password or password.startswith("replace-"):
            raise RuntimeError(f"Set {password_variable} to a unique password in your local .env file.")

        existing = mongo_db.users.find_one({"username": username})
        if existing:
            mongo_db.users.update_one(
                {"username": username},
                {"$set": {"name": name, "password_hash": generate_password_hash(password)}},
            )
        else:
            mongo_db.users.insert_one(
                {
                    "id": next_id("users"),
                    "name": name,
                    "username": username,
                    "password_hash": generate_password_hash(password),
                    "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )


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
    return mongo_db.users.find_one({"username": username})


def get_user_by_id(user_id):
    return document_by_id("users", user_id)


def partner_id(user_id):
    partner = mongo_db.users.find_one({"id": {"$ne": int(user_id)}}, sort=[("id", ASCENDING)])
    if partner:
        return partner.get("id")
    return None


def attach_user(document, user_id_field, name_field):
    if not document:
        return None
    result = dict(document)
    user = get_user_by_id(result.get(user_id_field))
    result[name_field] = user["name"] if user else "Unknown"
    return result


def get_latest_music():
    item = mongo_db.music_history.find_one(sort=[("created_at", DESCENDING), ("id", DESCENDING)])
    return attach_user(item, "user_id", "user_name")


def get_previous_music():
    row = next(mongo_db.music_history.find().sort([("created_at", DESCENDING), ("id", DESCENDING)]).skip(1).limit(1), None)
    return attach_user(row, "user_id", "user_name")


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
    photo_count = mongo_db.photos.count_documents({})
    message_count = mongo_db.messages.count_documents({})
    food_count = mongo_db.food_wishes.count_documents({})
    note_count = mongo_db.partner_notes.count_documents({})
    music_count = mongo_db.music_history.count_documents({})
    location_count = mongo_db.locations.count_documents({})
    latest_photo = mongo_db.photos.find_one(sort=[("created_at", DESCENDING), ("id", DESCENDING)])
    latest_photo = attach_user(latest_photo, "uploaded_by", "uploader")
    if latest_photo:
        uploader = get_user_by_id(latest_photo["uploaded_by"])
        latest_photo["uploader_username"] = uploader["username"] if uploader else ""
    latest_message = mongo_db.messages.find_one(sort=[("created_at", DESCENDING), ("id", DESCENDING)])
    latest_message = attach_user(latest_message, "sender_id", "sender_name")
    latest_music = get_latest_music()
    latest_note = mongo_db.partner_notes.find_one(sort=[("created_at", DESCENDING), ("id", DESCENDING)])
    latest_note = attach_user(latest_note, "user_id", "user_name")
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

        local_photo_path = Path(app.config["UPLOAD_FOLDER"]) / unique_name
        content_type = "image/gif" if unique_name.lower().endswith(".gif") else "image/webp"
        try:
            with local_photo_path.open("rb") as photo_stream:
                photo_bucket.upload_from_stream(
                    unique_name,
                    photo_stream,
                    metadata={"content_type": content_type},
                )
            local_photo_path.unlink(missing_ok=True)
        except Exception:
            local_photo_path.unlink(missing_ok=True)
            flash("The photo could not be stored in MongoDB. Please try again.", "danger")
            return redirect(url_for("gallery"))

        mongo_db.photos.insert_one({
            "id": next_id("photos"),
            "filename": unique_name,
            "caption": caption or "A treasured memory.",
            "uploaded_by": session["user_id"],
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        flash("Photo uploaded and optimized successfully.", "success")
        return redirect(url_for("gallery"))

    photos = [
        attach_user(photo, "uploaded_by", "uploader")
        for photo in mongo_db.photos.find().sort([("created_at", DESCENDING), ("id", DESCENDING)])
    ]
    for photo in photos:
        uploader = get_user_by_id(photo["uploaded_by"])
        photo["uploader_username"] = uploader["username"] if uploader else ""
    return render_template("gallery.html", photos=photos)


@app.route("/gallery/delete/<int:photo_id>", methods=["POST"])
@login_required
def delete_gallery_photo(photo_id):
    photo = document_by_id("photos", photo_id)
    if not photo:
        flash("Photo not found.", "warning")
        return redirect(url_for("gallery"))

    grid_file = next(photo_bucket.find({"filename": photo["filename"]}).sort("uploadDate", DESCENDING).limit(1), None)
    if grid_file:
        photo_bucket.delete(grid_file._id)
    local_photo_path = Path(app.config["UPLOAD_FOLDER"]) / photo["filename"]
    local_photo_path.unlink(missing_ok=True)

    mongo_db.photos.delete_one({"id": photo_id})
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
        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        mongo_db.messages.insert_one({
            "id": next_id("messages"),
            "sender_id": session["user_id"],
            "receiver_id": receiver_id,
            "message": message_text,
            "created_at": created_at,
            "updated_at": created_at,
        })
        flash("Your message was sent.", "success")
        return redirect(url_for("messages"))

    participant_ids = [session["user_id"], partner["id"]] if partner else [session["user_id"]]
    message_rows = list(mongo_db.messages.find({
        "sender_id": {"$in": participant_ids},
        "receiver_id": {"$in": participant_ids},
    }).sort([("created_at", DESCENDING), ("id", DESCENDING)]))
    for message in message_rows:
        sender = get_user_by_id(message["sender_id"])
        receiver = get_user_by_id(message["receiver_id"])
        message["sender_name"] = sender["name"] if sender else "Unknown"
        message["receiver_name"] = receiver["name"] if receiver else "Unknown"
    return render_template("messages.html", messages=message_rows, current_user=current_user, partner=partner)


@app.route("/messages/delete/<int:message_id>", methods=["POST"])
@login_required
def delete_message(message_id):
    item = document_by_id("messages", message_id)
    if not item:
        flash("Message not found.", "warning")
        return redirect(url_for("messages"))

    if item["sender_id"] != session["user_id"]:
        flash("You can only delete your own messages.", "danger")
        return redirect(url_for("messages"))

    mongo_db.messages.delete_one({"id": message_id})
    flash("Message deleted.", "success")
    return redirect(url_for("messages"))


@app.route("/messages/edit/<int:message_id>", methods=["POST"])
@login_required
def edit_message(message_id):
    new_message = (request.form.get("message") or "").strip()
    if not new_message:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("messages"))

    item = document_by_id("messages", message_id)
    if not item:
        flash("Message not found.", "warning")
        return redirect(url_for("messages"))

    if item["sender_id"] != session["user_id"]:
        flash("You can only edit your own messages.", "danger")
        return redirect(url_for("messages"))

    mongo_db.messages.update_one(
        {"id": message_id},
        {"$set": {"message": new_message, "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}},
    )
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

        mongo_db.music_history.insert_one({
            "id": next_id("music_history"),
            "user_id": session["user_id"],
            "song_title": title,
            "youtube_url": final_url,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        flash("Song saved successfully.", "success")
        return redirect(url_for("music"))

    latest = get_latest_music()
    previous = get_previous_music()
    history = [
        attach_user(item, "user_id", "user_name")
        for item in mongo_db.music_history.find().sort([("created_at", DESCENDING), ("id", DESCENDING)]).limit(10)
    ]
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

        mongo_db.food_wishes.insert_one({
            "id": next_id("food_wishes"),
            "user_id": session["user_id"],
            "food_name": food_name,
            "note": note,
            "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })
        flash("Food wish added.", "success")
        return redirect(url_for("food"))

    food_items = [
        attach_user(item, "user_id", "user_name")
        for item in mongo_db.food_wishes.find().sort([("created_at", DESCENDING), ("id", DESCENDING)])
    ]
    return render_template("food.html", food_items=food_items)


@app.route("/food/delete/<int:food_id>", methods=["POST"])
@login_required
def delete_food(food_id):
    item = document_by_id("food_wishes", food_id)
    if not item:
        flash("Food wish not found.", "warning")
        return redirect(url_for("food"))

    if item["user_id"] != session["user_id"]:
        flash("You can only delete your own food wish.", "danger")
        return redirect(url_for("food"))

    mongo_db.food_wishes.delete_one({"id": food_id})
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

    item = document_by_id("food_wishes", food_id)
    if not item:
        flash("Food wish not found.", "warning")
        return redirect(url_for("food"))

    if item["user_id"] != session["user_id"]:
        flash("You can only edit your own food wish.", "danger")
        return redirect(url_for("food"))

    mongo_db.food_wishes.update_one(
        {"id": food_id},
        {"$set": {"food_name": food_name, "note": note}},
    )
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

        created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        mongo_db.partner_notes.insert_one({
            "id": next_id("partner_notes"),
            "user_id": session["user_id"],
            "note": note_text,
            "status": status,
            "created_at": created_at,
            "updated_at": created_at,
        })
        flash("Your note is now shared.", "success")
        return redirect(url_for("mood_swings"))

    notes = [
        attach_user(item, "user_id", "user_name")
        for item in mongo_db.partner_notes.find().sort([("created_at", DESCENDING), ("id", DESCENDING)])
    ]
    return render_template("mood_swings.html", notes=notes)


@app.route("/mood-swings/delete/<int:note_id>", methods=["POST"])
@login_required
def delete_note(note_id):
    item = document_by_id("partner_notes", note_id)
    if not item:
        flash("Note not found.", "warning")
        return redirect(url_for("mood_swings"))

    if item["user_id"] != session["user_id"]:
        flash("You can only delete your own note.", "danger")
        return redirect(url_for("mood_swings"))

    mongo_db.partner_notes.delete_one({"id": note_id})
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

    item = document_by_id("partner_notes", note_id)
    if not item:
        flash("Note not found.", "warning")
        return redirect(url_for("mood_swings"))

    if item["user_id"] != session["user_id"]:
        flash("You can only edit your own note.", "danger")
        return redirect(url_for("mood_swings"))

    mongo_db.partner_notes.update_one(
        {"id": note_id},
        {"$set": {"note": note_text, "status": status, "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}},
    )
    flash("Note updated.", "success")
    return redirect(url_for("mood_swings"))


@app.route("/location", methods=["GET", "POST"])
@login_required
def location():
    recent_locations = [
        attach_user(item, "user_id", "user_name")
        for item in mongo_db.locations.find().sort([("created_at", DESCENDING), ("id", DESCENDING)])
    ]
    now_text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    active_live_locations = [
        attach_user(item, "user_id", "user_name")
        for item in mongo_db.live_locations.find({"expires_at": {"$gt": now_text}}).sort("updated_at", DESCENDING)
    ]
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

    mongo_db.locations.insert_one({
        "id": next_id("locations"),
        "user_id": session["user_id"],
        "latitude": lat_value,
        "longitude": lon_value,
        "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    })

    if request.is_json:
        return jsonify({"status": "Location shared successfully."})
    flash("Location spot pinned successfully.", "success")
    return redirect(url_for("location"))


@app.route("/api/location/live", methods=["GET", "POST"])
@login_required
def api_live_location():
    now = datetime.utcnow()
    now_text = now.strftime("%Y-%m-%d %H:%M:%S")

    if request.method == "GET":
        locations = [
            attach_user(item, "user_id", "user_name")
            for item in mongo_db.live_locations.find({"expires_at": {"$gt": now_text}}).sort("updated_at", DESCENDING)
        ]
        return jsonify({"locations": locations})

    data = request.get_json(silent=True) or request.form
    action = (data.get("action") or "").strip().lower()
    user_id = session["user_id"]

    if action == "stop":
        mongo_db.live_locations.delete_one({"user_id": user_id})
        return jsonify({"status": "stopped"})

    if action not in {"start", "update"}:
        return jsonify({"error": "Choose start, update, or stop."}), 400

    try:
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))
    except (TypeError, ValueError):
        return jsonify({"error": "Valid latitude and longitude are required."}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({"error": "Coordinates are outside the valid range."}), 400

    expires_at = (now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    if action == "start":
        mongo_db.live_locations.update_one(
            {"user_id": user_id},
            {"$set": {
                "latitude": latitude,
                "longitude": longitude,
                "started_at": now_text,
                "updated_at": now_text,
                "expires_at": expires_at,
            }, "$setOnInsert": {"user_id": user_id}},
            upsert=True,
        )
    else:
        result = mongo_db.live_locations.update_one(
            {"user_id": user_id, "expires_at": {"$gt": now_text}},
            {"$set": {"latitude": latitude, "longitude": longitude, "updated_at": now_text}},
        )
        if result.matched_count == 0:
            return jsonify({"error": "Live sharing has ended. Start sharing again."}), 409

    saved_location = mongo_db.live_locations.find_one({"user_id": user_id}, {"expires_at": 1})
    return jsonify({"status": "sharing", "expires_at": saved_location["expires_at"]})



@app.route("/location/delete/<int:location_id>", methods=["POST"])
@login_required
def delete_location(location_id):
    item = document_by_id("locations", location_id)
    if not item:
        flash("Location not found.", "warning")
        return redirect(url_for("location"))

    if item["user_id"] != session["user_id"]:
        flash("You can only delete your own location records.", "danger")
        return redirect(url_for("location"))

    mongo_db.locations.delete_one({"id": location_id})
    flash("Location history deleted.", "success")
    return redirect(url_for("location"))


@app.route("/uploads/photos/<path:filename>")
@login_required
def uploaded_photo(filename):
    grid_file = next(photo_bucket.find({"filename": filename}).sort("uploadDate", DESCENDING).limit(1), None)
    if grid_file:
        metadata = grid_file.metadata or {}
        return send_file(
            photo_bucket.open_download_stream(grid_file._id),
            mimetype=metadata.get("content_type", "application/octet-stream"),
            download_name=filename,
        )
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


with app.app_context():
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db()
    ensure_default_users()


if __name__ == "__main__":
    app.run(debug=DEBUG, host="127.0.0.1", port=5000)
