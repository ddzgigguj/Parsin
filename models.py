"""
Database models for MK match data storage.
Uses SQLite via aiosqlite.
"""

import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "matches.db")


async def init_db():
    """Initialize database and create tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER UNIQUE,
                time TEXT,
                date TEXT,
                match_number INTEGER,
                lobby INTEGER,
                player1_ru TEXT,
                player2_ru TEXT,
                player1_en TEXT,
                player2_en TEXT,
                p1m_coeff REAL,
                p2m_coeff REAL,
                p1_round_coeff REAL,
                p2_round_coeff REAL,
                fatality_coeff REAL,
                brutality_coeff REAL,
                no_finish_coeff REAL,
                fw_coeff REAL,
                total_matches TEXT,
                avg_time REAL,
                time_total_small REAL,
                time_small_over_coeff REAL,
                time_small_under_coeff REAL,
                time_small_tag TEXT,
                time_total_medium REAL,
                time_medium_over_coeff REAL,
                time_medium_under_coeff REAL,
                time_medium_tag TEXT,
                time_total_big REAL,
                time_big_over_coeff REAL,
                time_big_under_coeff REAL,
                time_big_tag TEXT,
                f_yes_coeff REAL,
                f_no_coeff REAL,
                bet_ids TEXT,
                score TEXT,
                total_rounds INTEGER,
                winner TEXT,
                has_rounds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                round_number INTEGER,
                winner TEXT,
                finish_type TEXT,
                time_seconds INTEGER,
                time_category TEXT,
                FOREIGN KEY (match_id) REFERENCES matches(id)
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_matches_message_id ON matches(message_id)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_rounds_match_id ON rounds(match_id)
        """)

        await db.commit()
    print(f"[DB] Database initialized at {DB_PATH}")


async def insert_match(match_data: dict) -> int:
    """Insert a match record and return its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT OR IGNORE INTO matches (
                message_id, time, date, match_number, lobby,
                player1_ru, player2_ru, player1_en, player2_en,
                p1m_coeff, p2m_coeff, p1_round_coeff, p2_round_coeff,
                fatality_coeff, brutality_coeff, no_finish_coeff, fw_coeff,
                total_matches, avg_time,
                time_total_small, time_small_over_coeff, time_small_under_coeff, time_small_tag,
                time_total_medium, time_medium_over_coeff, time_medium_under_coeff, time_medium_tag,
                time_total_big, time_big_over_coeff, time_big_under_coeff, time_big_tag,
                f_yes_coeff, f_no_coeff, bet_ids,
                score, total_rounds, winner, has_rounds
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?
            )
        """, (
            match_data.get('message_id'),
            match_data.get('time'),
            match_data.get('date'),
            match_data.get('match_number'),
            match_data.get('lobby'),
            match_data.get('player1_ru'),
            match_data.get('player2_ru'),
            match_data.get('player1_en'),
            match_data.get('player2_en'),
            match_data.get('p1m_coeff'),
            match_data.get('p2m_coeff'),
            match_data.get('p1_round_coeff'),
            match_data.get('p2_round_coeff'),
            match_data.get('fatality_coeff'),
            match_data.get('brutality_coeff'),
            match_data.get('no_finish_coeff'),
            match_data.get('fw_coeff'),
            match_data.get('total_matches'),
            match_data.get('avg_time'),
            match_data.get('time_total_small'),
            match_data.get('time_small_over_coeff'),
            match_data.get('time_small_under_coeff'),
            match_data.get('time_small_tag'),
            match_data.get('time_total_medium'),
            match_data.get('time_medium_over_coeff'),
            match_data.get('time_medium_under_coeff'),
            match_data.get('time_medium_tag'),
            match_data.get('time_total_big'),
            match_data.get('time_big_over_coeff'),
            match_data.get('time_big_under_coeff'),
            match_data.get('time_big_tag'),
            match_data.get('f_yes_coeff'),
            match_data.get('f_no_coeff'),
            match_data.get('bet_ids'),
            match_data.get('score'),
            match_data.get('total_rounds'),
            match_data.get('winner'),
            match_data.get('has_rounds', 0),
        ))
        await db.commit()
        return cursor.lastrowid


async def insert_rounds(match_id: int, rounds: list):
    """Insert round records for a match."""
    if not rounds:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("""
            INSERT INTO rounds (match_id, round_number, winner, finish_type, time_seconds, time_category)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [
            (match_id, r['round_number'], r['winner'], r['finish_type'], r['time_seconds'], r['time_category'])
            for r in rounds
        ])
        await db.commit()


async def get_match_count() -> int:
    """Get total number of matches in database."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM matches")
        row = await cursor.fetchone()
        return row[0]


async def get_last_message_id() -> int:
    """Get the last processed message ID for resuming."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT MAX(message_id) FROM matches")
        row = await cursor.fetchone()
        return row[0] or 0
