import mimetypes
from pathlib import Path

from gridfs import GridFSBucket
from pymongo import MongoClient

from config import MONGODB_DATABASE, MONGODB_URI, UPLOAD_FOLDER


def migrate_photos():
    if not MONGODB_URI:
        raise RuntimeError("Set MONGODB_URI in your local .env file before migrating photos.")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    database = client[MONGODB_DATABASE]
    bucket = GridFSBucket(database, bucket_name="uploads")
    uploaded = 0
    already_present = 0
    missing = 0

    try:
        client.admin.command("ping")
        for photo in database.photos.find({}, {"filename": 1}):
            filename = photo["filename"]
            existing = next(bucket.find({"filename": filename}).limit(1), None)
            if existing:
                already_present += 1
                continue

            local_path = Path(UPLOAD_FOLDER) / filename
            if not local_path.is_file():
                missing += 1
                continue

            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            with local_path.open("rb") as stream:
                bucket.upload_from_stream(
                    filename,
                    stream,
                    metadata={"content_type": content_type},
                )
            uploaded += 1
    finally:
        client.close()

    print(f"Photos uploaded to MongoDB GridFS: {uploaded}")
    print(f"Already present: {already_present}")
    print(f"Missing local files: {missing}")
    if missing:
        raise RuntimeError("Some photo files were not found; check uploads/photos before deploying.")


if __name__ == "__main__":
    migrate_photos()
