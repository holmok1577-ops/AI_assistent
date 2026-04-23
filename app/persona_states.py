import os

def get_persona_state(emotions: dict, relationships: dict) -> str:
    """
    Определяет текущее состояние персоны на основе эмоций и отношений
    и возвращает соответствующие инструкции.
    """
    instructions = []
    
    # Проверка низкой симпатии
    sympathy = relationships.get('sympathy', 50)
    if sympathy <= 30:
        instructions.append(load_state_file('low_sympathy.txt'))
    
    # Проверка высокого гнева/нервозности
    nervous = emotions.get('nervous', 0)
    if nervous >= 70:
        instructions.append(load_state_file('high_anger.txt'))
    
    # Проверка низкого спокойствия
    calm = emotions.get('calm', 50)
    if calm <= 30:
        instructions.append(load_state_file('low_calm.txt'))
    
    # Проверка высокой радости
    joy = emotions.get('joy', 50)
    if joy >= 70:
        instructions.append(load_state_file('high_joy.txt'))
    
    # Проверка высокой романтичности
    romantic = emotions.get('romantic', 0)
    if romantic >= 70:
        instructions.append(load_state_file('high_romantic.txt'))
    
    return "\n\n".join(instructions)

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
