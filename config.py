# config.py
from pymongo import MongoClient
import os

# PRODUCTION MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://gausewauser:qgE32Q7yYhV21jLz@cluster0.f1nxo9p.mongodb.net/")

client = MongoClient(MONGO_URI)
db = client["gausewa"]

cows_col = db["cows"]

JWT_SECRET = os.getenv("JWT_SECRET", "gausewa-secret-change-in-prod")
JWT_EXPIRE = 60