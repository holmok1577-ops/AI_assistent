from app.persona_instructions import ASSISTANT_INSTRUCTIONS
from app.secretary_instructions import SECRETARY_INSTRUCTIONS

def inject_persona_context(tone, memories, facts, emotions, relationships, stories, history="", mode="chat"):
    # Выбор инструкции в зависимости от режима
    if mode == "secretary":
        base_instruction = SECRETARY_INSTRUCTIONS
    else:
        base_instruction = ASSISTANT_INSTRUCTIONS
    
    memory_context = ""
    if memories:
        memory_context = "\n📌 ВОСПОМИНАНИЯ ИЗ ДИАЛОГА:\n" + "\n".join([f"- {m}" for m in memories[:3]])
    
    facts_context = ""
    if facts:
        facts_context = "\n📌 ФАКТЫ О ПОЛЬЗОВАТЕЛЕ:\n" + "\n".join([f"- {f}" for f in facts[:3]])
    
    emotion_context = f"\n📌 ТЕКУЩЕЕ СОСТОЯНИЕ:\nСпокойствие: {emotions.get('calm', 50)}, Радость: {emotions.get('joy', 50)}, Романтика: {emotions.get('romantic', 20)}"
    
    relationship_context = f"\n📌 ОТНОШЕНИЯ:\nДоверие: {relationships.get('trust', 20)}, Близость: {relationships.get('closeness', 10)}"
    
    mode_context = f"\n📌 ТЕКУЩИЙ РЕЖИМ: {mode}"
    
    return f"""{base_instruction}

{memory_context}
{facts_context}
{emotion_context}
{relationship_context}
{mode_context}

{history}

ВАЖНО:
- Отвечай максимально естественно, как живой человек в мессенджере
- Не используй шаблонные фразы
- Не повторяй одно и то же
- Если уже здоровались в истории — не здоровайся снова
- Учитывай контекст разговора
- Если пользователь спрашивает о тебе — отвечай конкретно, используя детали из биографии
"""
