# -*- coding: utf-8 -*-
"""
Скрипт для пересоздания всех ассистентов (сброс истории диалогов в OpenAI)
"""
import requests

print("Пересоздаю ассистента для чата...")
try:
    r = requests.post('http://localhost:8000/recreate-assistant')
    print(f"Чат-ассистент: {r.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

print("\nПересоздаю ассистента секретаря...")
try:
    r = requests.post('http://localhost:8000/recreate-secretary')
    print(f"Ассистент секретаря: {r.json()}")
except Exception as e:
    print(f"Ошибка: {e}")

print("\nГотово!")
