from aiogram import Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from typing import TypedDict
from utils.prompts import POSITION_INSTRUCTION_TEMPLATE, FINAL_SUMMARY_REQUEST
from utils.extract_position import extract_position
from bot.llm import ask_llm
from bot.memory import history_by_user, users

class TgUserData(TypedDict, total=False):
    state: str
    history: list
    position: str
    question_num: int
    answers: list

def register_handlers(dp: Dispatcher):
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

        user["answers"].append(text)
        user["question_num"] = user.get("question_num", 0) + 1
        history.append({"role": "user", "content": text})

        if user["question_num"] >= 10:
            user["state"] = "analyzing"
            await message.answer("Спасибо! Анализирую ваши ответы...")

            try:
                position = user.get("position", "не указана")
                prompt = FINAL_SUMMARY_REQUEST.format(position=position)

                full_history = "\n".join(
                    f"{msg['role'].capitalize()}: {msg['content']}" for msg in history if msg["role"] != "system"
                )
                final_prompt = {"role": "user", "content": prompt + "\n" + full_history}

                evaluation_history = [
                    {"role": "system", "content": "Ты — эксперт по подбору IT-специалистов. Твоя задача — проанализировать диалог и выбрать наиболее подходящую профессию для кандидата. Кандидат может врать"},
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
