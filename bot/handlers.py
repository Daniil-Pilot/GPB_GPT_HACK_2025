from aiogram import Dispatcher, types, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from typing import TypedDict
from utils.prompts import POSITION_INSTRUCTION_TEMPLATE, FINAL_SUMMARY_REQUEST
from utils.extract_position import extract_position
from bot.llm import ask_llm, is_valid_history
from bot.memory import history_by_user, users, last_message_id_by_user, user_locks
import re

STARTER_PHRASES = [
    "Здравствуйте! Напишите, на какую позицию Вы хотите пройти собеседование.",
    "Здравствуйте! Укажите вакансию, на которую хотите пройти собеседование.",
]

def should_start_dialog(history: list[str]) -> bool:
    if not history:
        return False
    return any(phrase in history[0] for phrase in STARTER_PHRASES)

class TgUserData(TypedDict, total=False):
    num_message: int
    state: str
    role_id: int
    history: list
    position: str
    question_num: int
    answers: list

def register_handlers(dp: Dispatcher):

    @dp.channel_post(Command("start"))
    async def start_interview(message: Message, command: CommandObject):
        cid = message.chat.id
        arg = command.args
        if arg is None:
            await message.answer("Бот запущен с некорректным параметром. Укажите номер личности, например: /start 0")
            return

        try:
            personality_id = int(arg)
            if not 0 <= personality_id <= 4:
                raise ValueError()
        except ValueError:
            await message.answer("Неверный параметр. Введите от 0 до 4. Пример: /start 2")
            return

        users[cid] = TgUserData(
            num_message=0,
            state="active",
            role_id=personality_id,
            question_num=0,
            answers=[]
        )
        history_by_user[cid] = []

    @dp.channel_post(F.text)
    async def handle_message(message: Message):
        cid = message.chat.id
        text = message.text.strip()

        if cid not in users:
            users[cid] = TgUserData(
                num_message=0,
                state="active",
                role_id=0,
                question_num=0,
                answers=[]
            )
            history_by_user[cid] = []
            await message.answer("Здравствуйте! Напишите, на какую позицию Вы хотите пройти собеседование.")
            return

        user = users[cid]
        if user.get("state") != "active":
            return

        history = history_by_user.setdefault(cid, [])

        if "position" not in user:
            position = extract_position(text)
            if not position:
                await message.answer("Пожалуйста, укажите позицию, на которую хотите пройти собеседование.")
                return
            user["position"] = position

            system_prompt = POSITION_INSTRUCTION_TEMPLATE.format(position=position)
            history.append({"role": "system", "content": system_prompt})
            history.append({"role": "user", "content": text})

            try:
                response = await ask_llm(history)
                if not response:
                    raise ValueError("LLM вернул пустой ответ.")
                history.append({"role": "assistant", "content": response})
                await message.answer(response)
            except Exception as e:
                print(f"[LLM ERROR] {e}")
                await message.answer("Ошибка при обращении к LLM.")
            return

        user.setdefault("answers", []).append(text)
        user["question_num"] = user.get("question_num", 0) + 1
        history.append({"role": "user", "content": text})

        if user["question_num"] >= 10:
            user["state"] = "analyzing"
            await message.answer("Спасибо! Анализирую ваши ответы...")

            history.append({"role": "user", "content": FINAL_SUMMARY_REQUEST})

            try:
                prompt = (
                    "На основе диалога ниже выбери наиболее подходящую позицию из списка:"
                    "- Data Scientist"
                    "- Data Engineer"
                    "- Data Analyst"
                    "- MLOps Engineer"
                    "- Project Manager"
                    "Укажи только одну из позиций из списка."
                    "Диалог:"
                )

                full_history = "\n".join(
                    f"{msg['role'].capitalize()}: {msg['content']}" for msg in history if msg["role"] != "system"
                )
                final_prompt = {"role": "user", "content": prompt + full_history}

                evaluation_history = [
                    {"role": "system", "content": "Ты — эксперт по подбору IT-специалистов. Твоя задача — проанализировать диалог и выбрать наиболее подходящую профессию для кандидата."},
                    final_prompt
                ]

                final_position = await ask_llm(evaluation_history)
                final_position = final_position.strip()

            except Exception as e:
                print(f"Final position evaluation error: {e}")
                await message.answer("Произошла ошибка при анализе ваших ответов.")
                return

            desired_position = user.get("position") or "не указана"

            if final_position.lower() == desired_position.lower():
                verdict = f"Отлично! Вы подходите на позицию {final_position}."
            else:
                verdict = (
                    f"Вы указали позицию '{desired_position}', но по результатам собеседования вам больше всего подходит позиция: {final_position}."
                )

            await message.answer(f"Вердикт: {verdict}")
            return

        try:
            response = await ask_llm(history)
            if not response:
                raise ValueError("LLM вернул пустой ответ.")
            history.append({"role": "assistant", "content": response})
            await message.answer(response)
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            await message.answer("Ошибка при обращении к LLM.")

    @dp.channel_post(~F.text)
    async def reject_non_text(message: Message):
        await message.answer("Бот принимает только текстовые сообщения.")
