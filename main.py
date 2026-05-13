"""
Telegram channel parser bot.
Parses MK match data from t.me/statamk10 and stores in SQLite database.
Uses Telethon for Telegram API access.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from models import init_db, insert_match, insert_rounds, get_match_count, get_last_message_id
from parser import parse_message

# Load environment variables
load_dotenv()

API_ID = int(os.getenv('TELETHON_API_ID'))
API_HASH = os.getenv('TELETHON_API_HASH')
SESSION_NAME = os.getenv('TELETHON_SESSION', 'telegram_session')
CHANNEL = os.getenv('CHANNEL', 'statamk10')

# Batch size for processing messages
BATCH_SIZE = 100
# How often to print progress
PROGRESS_INTERVAL = 1000


async def main():
    """Main function to parse channel messages."""
    print("=" * 60)
    print("  MK Match Parser - Telegram Channel Scraper")
    print("=" * 60)

    # Initialize database
    await init_db()

    # Get last processed message ID for resuming
    last_msg_id = await get_last_message_id()
    current_count = await get_match_count()
    print(f"[INFO] Database has {current_count} matches")
    if last_msg_id:
        print(f"[INFO] Resuming from message ID: {last_msg_id}")

    # Connect to Telegram
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()

    print(f"[INFO] Connected to Telegram")
    print(f"[INFO] Target channel: {CHANNEL}")

    try:
        # Get channel entity
        channel = await client.get_entity(CHANNEL)
        print(f"[INFO] Channel found: {channel.title}")

        # Count messages
        total_messages = 0
        parsed_count = 0
        skipped_count = 0
        error_count = 0

        # Iterate over all messages (oldest first for consistent ordering)
        # min_id=last_msg_id allows resuming from last processed message
        print(f"\n[PARSING] Starting to parse messages...")
        print(f"[PARSING] This may take a while for ~300k messages...")
        print("-" * 60)

        batch_matches = []
        batch_rounds = []

        async for message in client.iter_messages(
            channel,
            min_id=last_msg_id if last_msg_id else 0,
            reverse=True,  # Oldest first
        ):
            total_messages += 1

            if not message.text:
                skipped_count += 1
                continue

            try:
                match_data = parse_message(message.text, message.id)

                if match_data is None:
                    skipped_count += 1
                    continue

                # Extract rounds before inserting
                rounds = match_data.pop('rounds', [])

                # Insert match
                match_id = await insert_match(match_data)

                if match_id and rounds:
                    await insert_rounds(match_id, rounds)

                parsed_count += 1

            except Exception as e:
                error_count += 1
                if error_count <= 10:
                    print(f"[ERROR] Message {message.id}: {e}")
                elif error_count == 11:
                    print("[ERROR] Suppressing further error messages...")

            # Progress report
            if total_messages % PROGRESS_INTERVAL == 0:
                print(
                    f"[PROGRESS] Processed: {total_messages} | "
                    f"Parsed: {parsed_count} | "
                    f"Skipped: {skipped_count} | "
                    f"Errors: {error_count}"
                )

    except FloodWaitError as e:
        print(f"\n[FLOOD] Telegram rate limit hit. Wait {e.seconds} seconds.")
        print(f"[FLOOD] Progress saved. Re-run the script to continue.")

    except KeyboardInterrupt:
        print(f"\n[INTERRUPTED] Stopping gracefully...")

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Final stats
        final_count = await get_match_count()
        print("\n" + "=" * 60)
        print(f"  PARSING COMPLETE")
        print(f"  Total messages scanned: {total_messages}")
        print(f"  Matches parsed: {parsed_count}")
        print(f"  Messages skipped: {skipped_count}")
        print(f"  Errors: {error_count}")
        print(f"  Total matches in DB: {final_count}")
        print("=" * 60)

        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
