"""
Data storage for MK match data.
Uses JSON file for storage.
"""

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "matches.json")


def _load_data() -> dict:
    """Load data from JSON file."""
    if not os.path.exists(DATA_PATH):
        return {"matches": [], "last_message_id": 0}
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: dict):
    """Save data to JSON file."""
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def init_db():
    """Initialize JSON storage file."""
    if not os.path.exists(DATA_PATH):
        _save_data({"matches": [], "last_message_id": 0})
    print(f"[DB] JSON storage at {DATA_PATH}")


async def insert_match(match_data: dict) -> int:
    """Insert a match record into JSON. Returns index."""
    data = _load_data()

    # Check if message already exists (avoid duplicates)
    msg_id = match_data.get('message_id')
    for m in data['matches']:
        if m.get('message_id') == msg_id:
            return -1  # Already exists

    data['matches'].append(match_data)

    # Update last message ID
    if msg_id and msg_id > data['last_message_id']:
        data['last_message_id'] = msg_id

    _save_data(data)
    return len(data['matches']) - 1


async def insert_rounds(match_id: int, rounds: list):
    """Insert rounds into the match record."""
    if not rounds or match_id < 0:
        return
    data = _load_data()
    if match_id < len(data['matches']):
        data['matches'][match_id]['rounds'] = rounds
        _save_data(data)


async def get_match_count() -> int:
    """Get total number of matches in storage."""
    data = _load_data()
    return len(data['matches'])


async def get_last_message_id() -> int:
    """Get the last processed message ID for resuming."""
    data = _load_data()
    return data.get('last_message_id', 0)


async def save_batch(matches: list):
    """Save a batch of matches at once (more efficient for large imports)."""
    data = _load_data()

    existing_ids = {m.get('message_id') for m in data['matches']}

    added = 0
    for match in matches:
        msg_id = match.get('message_id')
        if msg_id not in existing_ids:
            data['matches'].append(match)
            existing_ids.add(msg_id)
            if msg_id and msg_id > data['last_message_id']:
                data['last_message_id'] = msg_id
            added += 1

    if added > 0:
        _save_data(data)

    return added
