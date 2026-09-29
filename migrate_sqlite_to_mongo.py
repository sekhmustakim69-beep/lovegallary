import sqlite3
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient

from config import DATABASE_URL, MONGODB_DATABASE, MONGODB_URI

COLLECTIONS = (
    "users",
    "photos",
    "messages",
    "music_history",
    "food_wishes",
    "partner_notes",
    "locations",
    "live_locations",
)


def migrate():
    source_path = Path(DATABASE_URL)
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite source database not found: {source_path}")
    if not MONGODB_URI:
        raise RuntimeError("Set MONGODB_URI in your local .env file before migrating.")

    sqlite_connection = sqlite3.connect(source_path)
    sqlite_connection.row_factory = sqlite3.Row
    mongo_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=10000)
    mongo_db = mongo_client[MONGODB_DATABASE]

    try:
        mongo_client.admin.command("ping")
        migration_id = "sqlite-love-db-v1"
        if mongo_db.migration_state.find_one({"_id": migration_id}):
            print("SQLite data has already been migrated; no changes were made.")
            return

        source_tables = {
            row[0]
            for row in sqlite_connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        missing_tables = set(COLLECTIONS) - source_tables
        if missing_tables:
            raise RuntimeError("SQLite database is missing collections: " + ", ".join(sorted(missing_tables)))

        source_users = [dict(row) for row in sqlite_connection.execute("SELECT * FROM users ORDER BY id")]
        existing_users = list(mongo_db.users.find({}, {"id": 1, "username": 1}))
        expected_users = {(user["id"], user["username"]) for user in source_users}
        current_users = {(user.get("id"), user.get("username")) for user in existing_users}
        if current_users and current_users != expected_users:
            raise RuntimeError("MongoDB already has different users; refusing to overwrite them.")

        for collection_name in COLLECTIONS:
            existing_count = mongo_db[collection_name].count_documents({})
            if collection_name != "users" and existing_count:
                raise RuntimeError(
                    f"MongoDB collection '{collection_name}' is not empty; refusing to overwrite it."
                )

        migrated_counts = {}
        for collection_name in COLLECTIONS:
            source_rows = sqlite_connection.execute(f"SELECT * FROM {collection_name}").fetchall()
            documents = []
            for row in source_rows:
                document = dict(row)
                if "id" not in document:
                    document["id"] = document["user_id"]
                documents.append(document)

            if collection_name == "users":
                for document in documents:
                    mongo_db.users.replace_one({"id": document["id"]}, document, upsert=True)
            elif documents:
                mongo_db[collection_name].insert_many(documents)

            migrated_counts[collection_name] = len(documents)
            if collection_name != "live_locations" and documents:
                mongo_db.counters.update_one(
                    {"_id": collection_name},
                    {"$max": {"value": max(document["id"] for document in documents)}},
                    upsert=True,
                )

        mongo_db.migration_state.insert_one({
            "_id": migration_id,
            "source": str(source_path.name),
            "completed_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "counts": migrated_counts,
        })
        print("SQLite records migrated successfully:")
        for collection_name, count in migrated_counts.items():
            print(f"  {collection_name}: {count}")
    finally:
        sqlite_connection.close()
        mongo_client.close()


if __name__ == "__main__":
    migrate()
