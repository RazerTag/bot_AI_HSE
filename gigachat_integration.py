# gigachat_integration.py

import requests
import os
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def generate_text_gigachat(user_prompt: str) -> str:
    """
    Отправляем запрос к GigaChat API, чтобы получить ответ assistant'а.
    user_prompt — это строка, которая пойдёт в "content" для "user".

    Возвращаем текст ответа от GigaChat (или сообщение об ошибке).
    """
    # Берём токен из .env или из другого места
    token = os.getenv("GIGACHAT_TOKEN")  # Важно: нужно прописать GIGACHAT_TOKEN=... в .env

    if not token:
        return "Ошибка: GigaChat-токен не найден."

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    payload = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "stream": False,
        "repetition_penalty": 1
    }

    headers = {
      "Content-Type": "application/json",
      "Accept": "application/json",
      "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30, verify=False)
        data = response.json()

        # Проверка на ошибку
        if "choices" not in data:
            return f"Ошибка от GigaChat API: {data}"

        # Берём текст из первого choice
        answer_content = data["choices"][0]["message"]["content"]
        return answer_content.strip()
    except Exception as e:
        return f"Ошибка при обращении к GigaChat: {e}"