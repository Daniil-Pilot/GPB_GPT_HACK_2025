import asyncio
from collections import defaultdict
from bot.main import start_bot

history_by_user = defaultdict(list)
users = defaultdict(dict)
last_message_id_by_user = {}
user_locks = defaultdict(asyncio.Lock)

if __name__ == "__main__":
    asyncio.run(start_bot())