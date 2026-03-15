from config import client, db

try:
    client.admin.command("ping")
    print("✅ MongoDB connected successfully")

    print("Database:", db.name)
    print("Collections:", db.list_collection_names())

except Exception as e:
    print("❌ Database connection failed")
    print(e)