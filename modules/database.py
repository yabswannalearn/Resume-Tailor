"""
Database Module for Resume Tailor Agent.

PURPOSE:
This is the centralized MongoDB connection manager. Instead of every
module creating its own database connection, they all go through here.

HOW IT WORKS:
1. Reads the MONGODB_URI from your .env file
2. Creates a single MongoClient connection (reused across all requests)
3. Provides helper functions to access the database and collections

WHY MONGODB ATLAS:
- Your agent memory (past sessions) is now stored in the cloud
- Data persists even if you restart the server or switch machines
- You can view your data in the Atlas web UI
- Easy to scale later if you add more features (user accounts, etc.)
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ─── Connection Setup ─────────────────────────────────────
# We create ONE client that gets reused. MongoClient handles
# connection pooling internally, so this is efficient.

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = "resume_tailor"

# The client is created at module load time (when the server starts).
# It stays alive for the lifetime of the app.
_client = None


def get_client() -> MongoClient:
    """
    Get or create the MongoDB client.
    Uses lazy initialization — the connection is only made
    the first time this is called.
    """
    global _client
    if _client is None:
        if not MONGODB_URI:
            raise ValueError(
                "MONGODB_URI not found in .env file. "
                "Please add your MongoDB Atlas connection string."
            )
        _client = MongoClient(MONGODB_URI)
    return _client


def get_db():
    """
    Get the 'resume_tailor' database.
    This is the main database where all collections live.
    """
    return get_client()[DB_NAME]


def get_collection(name: str):
    """
    Get a specific collection by name.

    Collections used:
    - 'sessions': Agent memory (past goals, tools used, summaries)
    - 'resumes':  Generated tailored resumes (for history)
    """
    return get_db()[name]


def test_connection() -> bool:
    """
    Test if the MongoDB connection is working.
    Returns True if connected, raises an exception if not.
    """
    client = get_client()
    # This forces a round-trip to the server
    client.admin.command("ping")
    return True
