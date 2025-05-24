from collections import defaultdict
import asyncio

history_by_user = defaultdict(list)
users = defaultdict(dict)
last_message_id_by_user = {}
user_locks = defaultdict(asyncio.Lock)
