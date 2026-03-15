# config.py
from pymongo import MongoClient
import os

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://gausewauser:gausewauser7054@cluster0.f1nxo9p.mongodb.net/?appName=Cluster0"
)

client = MongoClient(MONGO_URI)

db = client["gausewa"]

# Collections
cows_col = db["cows"]

# JWT Settings
JWT_SECRET = os.getenv("JWT_SECRET", "gausewa-secret-change-in-prod")
JWT_EXPIRE = 60

