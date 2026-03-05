"""
Memory System for Resume Tailor Agent (MongoDB-backed).

PURPOSE:
This module gives the agent long-term memory by saving past sessions
to MongoDB Atlas. Before this upgrade, sessions were saved to a local
JSON file — now they persist in the cloud.

HOW IT WORKS:
- After each agent session, we save a document to the 'sessions' collection
- Before each new session, we query the last N sessions as context
- The agent sees a formatted summary of past sessions in its system prompt

WHAT CHANGED FROM THE JSON VERSION:
- save_session() → now does db.sessions.insert_one() instead of file write
- load_past_sessions() → now does db.sessions.find() instead of file read
- No more local files in memory/ directory needed
"""

from datetime import datetime
from modules.database import get_collection


def load_past_sessions(limit: int = 5) -> list:
    """
    Load the most recent sessions from MongoDB.
    Returns a list of session dicts, sorted by most recent last.
    
    The MongoDB query:
    - Sorts by timestamp descending (newest first)
    - Limits to N results
    - Then we reverse so oldest is first (chronological order)
    """
    collection = get_collection("sessions")

    # Find the last N sessions, sorted newest first
    cursor = collection.find(
        {},  # no filter — get all sessions
        {"_id": 0}  # exclude MongoDB's internal _id field from results
    ).sort("timestamp", -1).limit(limit)

    # Convert cursor to list and reverse for chronological order
    sessions = list(cursor)
    sessions.reverse()

    return sessions


def save_session(goal: str, steps: list, summary: str):
    """
    Save a completed agent session to MongoDB.

    This creates a document like:
    {
        "timestamp": "2026-03-05T12:30:00",
        "goal": "Tailor my resume for Google SWE role",
        "tools_used": ["analyze_job", "load_identity", "build_resume", "generate_pdf"],
        "summary": "I analyzed the job, loaded your profile, and generated a tailored PDF."
    }
    """
    collection = get_collection("sessions")

    collection.insert_one({
        "timestamp": datetime.now().isoformat(),
        "goal": goal,
        "tools_used": steps,
        "summary": summary,
    })


def format_memory_for_prompt(limit: int = 5) -> str:
    """
    Format past sessions into a readable string for the agent's prompt.
    This is what gets injected into the system message so the agent
    knows what it has done before.

    (This function is unchanged — it just reads from MongoDB now
    instead of JSON, since load_past_sessions() was updated.)
    """
    sessions = load_past_sessions(limit)
    if not sessions:
        return "No previous sessions found. This is the first interaction."

    lines = ["Here are your recent past sessions with this user:"]
    for i, s in enumerate(sessions, 1):
        lines.append(
            f"\n**Session {i}** ({s['timestamp']}):\n"
            f"  Goal: {s['goal']}\n"
            f"  Tools used: {', '.join(s['tools_used'])}\n"
            f"  Result: {s['summary']}"
        )

    return "\n".join(lines)
