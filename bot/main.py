import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from bot.llm import is_valid_history

from bot.handlers import register_handlers

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

async def start_bot():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    register_handlers(dp)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
