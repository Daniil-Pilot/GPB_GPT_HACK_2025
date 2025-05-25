import re

POSITIONS = {
    "data scientist": "Data Scientist",
    "дата сайентист": "Data Scientist",
    "дата саинтист": "Data Scientist",
    "дата саентист": "Data Scientist",
    "дата сциентист": "Data Scientist",
    "data engineer": "Data Engineer",
    "дата инженер": "Data Engineer",
    "data analyst": "Data Analyst",
    "дата аналитик": "Data Analyst",
    "mlops engineer": "MLOps Engineer",
    "mlops": "MLOps Engineer",
    "project manager": "Project Manager",
    "пм": "Project Manager",
    "проджект менеджер": "Project Manager",
    "проджект": "Project Manager",
}

def should_start_dialog(messages: list[str]) -> bool:
    first_message = messages[0].lower()
    trigger_phrases = [
        "привет", "здравствуйте", "добрый день", "начнем", "начинаем",
        "я представляю", "расскажите о себе", "давайте начнем"
    ]
    return any(phrase in first_message for phrase in trigger_phrases)


def extract_position(text: str) -> str | None:
    text = text.lower()

    for keyword, position in POSITIONS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            return position

    return None
