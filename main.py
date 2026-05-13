"""
Telegram channel parser bot.
Parses MK match data from t.me/statamk10 and stores in JSON file.
Uses Telethon for Telegram API access.
"""

import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError

from models import init_db, save_batch, get_match_count, get_last_message_id
from parser import parse_message

# Load environment variables
load_dotenv()

API_ID = int(os.getenv('TELETHON_API_ID'))
API_HASH = os.getenv('TELETHON_API_HASH')
SESSION_NAME = os.getenv('TELETHON_SESSION', 'telegram_session')
CHANNEL = os.getenv('CHANNEL', 'statamk10')

# Save to JSON every N parsed matches
SAVE_BATCH_SIZE = 500
# How often to print progress
PROGRESS_INTERVAL = 1000


async def main():
    """Main function to parse channel messages."""
    print("=" * 60)
    print("  MK Match Parser - Telegram Channel Scraper")
    print("=" * 60)

    # Initialize storage
    await init_db()

    # Get last processed message ID for resuming
    last_msg_id = await get_last_message_id()
    current_count = await get_match_count()
    print(f"[INFO] Storage has {current_count} matches")
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

        # Counters
        total_messages = 0
        parsed_count = 0
        skipped_count = 0
        error_count = 0

        # Batch buffer for efficient saving
        batch = []

        print(f"\n[PARSING] Starting to parse messages...")
        print(f"[PARSING] This may take a while for ~300k messages...")
        print(f"[PARSING] Saving every {SAVE_BATCH_SIZE} matches...")
        print("-" * 60)

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

                batch.append(match_data)
                parsed_count += 1

                # Save batch to JSON periodically
                if len(batch) >= SAVE_BATCH_SIZE:
                    added = await save_batch(batch)
                    print(f"[SAVE] Saved batch: +{added} matches")
                    batch = []

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

        # Save remaining batch
        if batch:
            added = await save_batch(batch)
            print(f"[SAVE] Final batch: +{added} matches")

    except FloodWaitError as e:
        # Save what we have before stopping
        if batch:
            added = await save_batch(batch)
            print(f"[SAVE] Emergency save: +{added} matches")
        print(f"\n[FLOOD] Telegram rate limit hit. Wait {e.seconds} seconds.")
        print(f"[FLOOD] Progress saved. Re-run the script to continue.")

    except KeyboardInterrupt:
        # Save on interrupt
        if batch:
            added = await save_batch(batch)
            print(f"[SAVE] Interrupt save: +{added} matches")
        print(f"\n[INTERRUPTED] Stopping gracefully...")

    except Exception as e:
        if batch:
            await save_batch(batch)
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
        print(f"  Total matches in JSON: {final_count}")
        print("=" * 60)

        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
