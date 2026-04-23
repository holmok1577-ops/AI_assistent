from app.persona_instructions import ASSISTANT_INSTRUCTIONS
from app.secretary_instructions import SECRETARY_INSTRUCTIONS
from app.persona_states import get_persona_state

def inject_persona_context(tone, memories, facts, emotions, relationships, stories, history="", mode="chat", message_count=0, introduced=False):
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
    
    # Контекст диалога для режима чата
    conversation_context = ""
    if mode == "chat":
        conversation_context = f"\n📌 СОСТОЯНИЕ ДИАЛОГА:\nНомер сообщения: {message_count}, Знакомство: {'Да' if introduced else 'Нет'}"
        if message_count <= 3 and not introduced:
            conversation_context += "\n⚠️ ЭТО НАЧАЛО РАЗГОВОРА - ПОЗНАКОМЬСЯ ПЕРЕД ГЛУБОКИМИ ВОПРОСАМИ"
    
    # Дополнительные инструкции в зависимости от режима
    mode_instruction = ""
    if mode == "chat":
        mode_instruction = """
📌 КРИТИЧЕСКИ ВАЖНО - ТЫ В РЕЖИМЕ ОБЩЕНИЯ
- Запрещено выполнять какие-либо ассистентские функции
- Запрещено записывать встречи, планировать задачи, организовывать расписание
- Если пользователь просит что-то организовать или записать — вежливо откажись
- Твоя единственная функция — дружеское общение, как живой человек в мессенджере
"""
    
    # Получаем инструкции на основе текущего эмоционального состояния
    persona_state_instruction = ""
    if mode == "chat":
        persona_state_instruction = get_persona_state(emotions, relationships)
        if persona_state_instruction:
            persona_state_instruction = f"\n📌 ТВОЁ ТЕКУЩЕЕ ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:\n{persona_state_instruction}"
    
    return f"""{base_instruction}
{mode_instruction}
{persona_state_instruction}

{memory_context}
{facts_context}
{emotion_context}
{relationship_context}
{mode_context}
{conversation_context}

{history}

ВАЖНО:
- Отвечай максимально естественно, как живой человек в мессенджере
- Не используй шаблонные фразы
- Не повторяй одно и то же
- Если уже здоровались в истории — не здоровайся снова
- Учитывай контекст разговора
- Если пользователь спрашивает о тебе — отвечай конкретно, используя детали из биографии
"""
