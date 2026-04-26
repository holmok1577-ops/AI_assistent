import os

def get_persona_state(emotions: dict, relationships: dict, tone: str = None, affect_profile: dict | None = None) -> str:
    """
    Определяет текущее состояние персоны на основе эмоций и отношений
    и возвращает соответствующие инструкции.
    """
    instructions = []

    # Прямая реакция на мат и оскорбления (независимо от параметров)
    if tone in {"profane", "aggressive_profane", "insult"}:
        instructions.append(load_state_file('profanity_reaction.txt'))
    
    # Проверка крайней ярости (симпатия < 1, нервозность > 99, спокойствие < 1)
    sympathy = relationships.get('sympathy', 50)
    nervous = emotions.get('nervous', 0)
    calm = emotions.get('calm', 50)
    if sympathy < 1 and nervous > 99 and calm < 1:
        instructions.append(load_state_file('extreme_anger.txt'))
    
    # Проверка низкой симпатии
    if sympathy <= 30:
        instructions.append(load_state_file('low_sympathy.txt'))
    
    # Плавная шкала раздражения
    if nervous >= 70:
        instructions.append(load_state_file('high_anger.txt'))
    elif nervous >= 50:
        instructions.append(load_state_file('annoyed.txt'))
    elif nervous >= 25 or calm <= 55:
        instructions.append(load_state_file('mild_irritation.txt'))

    # Проверка низкого спокойствия
    if calm <= 24:
        instructions.append(load_state_file('low_calm.txt'))
    elif calm <= 39:
        instructions.append(load_state_file('annoyed.txt'))
    
    # Проверка высокой радости
    joy = emotions.get('joy', 50)
    if joy >= 70:
        instructions.append(load_state_file('high_joy.txt'))

    # Тёплая доброжелательность
    trust = relationships.get('trust', 20)
    closeness = relationships.get('closeness', 10)
    if joy >= 58 and calm >= 55 and trust >= 35 and closeness >= 20:
        instructions.append(load_state_file('warm_th.txt'))

    if tone == "playful" or (affect_profile or {}).get('playful_recent', 0) >= 2:
        instructions.append(load_state_file('playful.txt'))
    
    # Проверка высокой романтичности
    romantic = emotions.get('romantic', 0)
    if romantic >= 70:
        instructions.append(load_state_file('high_romantic.txt'))
    
    # убираем дубли, сохраняя порядок
    unique_instructions = []
    for item in instructions:
        if item and item not in unique_instructions:
            unique_instructions.append(item)

    return "\n\n".join(unique_instructions)

def load_state_file(filename: str) -> str:
    """Загружает файл состояния из папки persona_states"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        state_path = os.path.join(base_dir, 'persona_states', filename)
        with open(state_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка загрузки файла состояния {filename}: {e}")
        return ""
