from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()

INSULT_KEYWORDS = [
    'туп', 'идиот', 'дур', 'дебил', 'кретин', 'ничтож', 'мраз', 'урод', 'сука',
    'шлюх', 'сучк', 'падла', 'твар', 'мудак', 'гнид', 'пидор', 'пидорас', 'уеби',
]

PROFANITY_KEYWORDS = [
    'бля', 'блять', 'блядь', 'бляди', 'блядки', 'блядский',
    'хуй', 'хуя', 'хую', 'хуем', 'хуйня', 'хуи', 'хуёв', 'хуёвая', 'хуёвый',
    'пизда', 'пизды', 'пизде', 'пизду', 'пиздой', 'пиздё', 'пиздёнок', 'пиздабол',
    'ебать', 'ебаный', 'ебаная', 'ебану', 'ебанут', 'ебануть', 'ебанись', 'ебись', 'ёб',
    'нахер', 'нахрен', 'нахуй', 'нахуя', 'нахера', 'нахрена',
    'ёбаный', 'ёбанный', 'ёбнутый', 'ёб твою мать',
    'гандон', 'гондон', 'гандоны', 'гондоны',
    'дроч', 'дрочить', 'дрочен', 'дрочила',
    'хер', 'хера', 'херу', 'хером',
    'жопа', 'жопы', 'жопе', 'жопой', 'жопу',
    'срать', 'сру', 'срёт', 'срёшь', 'срал', 'срала',
    'пиздец', 'пиздеца', 'пиздцом', 'пиздецкий',
    'гавно', 'гавна', 'гавном', 'гавнюк'
]

WARM_KEYWORDS = [
    'спасибо', 'спасиб', 'солныш', 'милая', 'хорошая', 'умница', 'приятно',
    'обожаю', 'нравишься', 'рад тебя', 'люблю', 'нежн', 'тепло', 'дорогая'
]

PLAYFUL_KEYWORDS = [
    'ахаха', 'аха', 'хаха', 'лол', 'ржу', 'шутк', 'смешно', 'забавно',
    'ору', 'угар', 'прикол', 'мем', ':)', ')))'
]


def detect_tone(text: str):
    logger.info(f"[Sentiment] Определение тона для сообщения: {text[:50]}...")
    score = analyzer.polarity_scores(text)["compound"]
    text_lower = text.lower()

    profanity_count = sum(1 for keyword in PROFANITY_KEYWORDS if keyword in text_lower)
    insult_count = sum(1 for keyword in INSULT_KEYWORDS if keyword in text_lower)
    warmth_count = sum(1 for keyword in WARM_KEYWORDS if keyword in text_lower)
    playful_count = sum(1 for keyword in PLAYFUL_KEYWORDS if keyword in text_lower)

    if profanity_count >= 2 or (profanity_count >= 1 and insult_count >= 1):
        result = "aggressive_profane"
    elif insult_count >= 1:
        result = "insult"
    elif profanity_count >= 1:
        result = "profane"
    # Проверка на вопросы о роботах/ИИ
    elif any(keyword in text_lower for keyword in ['ты робот', 'ты ии', 'искусственный интеллект', 'ai', 'программа', 'бот', 'алгоритм', 'машина', 'компьютер']):
        result = "robot_question"
    # Проверка на извинения по ключевым словам
    elif any(keyword in text_lower for keyword in ['прости', 'прошу прощения', 'извини', 'простите', 'не хотел обидеть', 'не хотела обидеть', 'виноват', 'виновата', 'сорян', 'извеняюсь', 'извиняюсь']):
        result = "apologetic"
    # Проверка на флирт по ключевым словам
    elif any(keyword in text_lower for keyword in ['люблю', 'нравишься', 'красивая', 'милая', 'обнимаю', 'целую', 'соскучился', 'хочу тебя']):
        result = "flirty"
    elif playful_count >= 1:
        result = "playful"
    elif warmth_count >= 1:
        result = "warm"
    # Проверка на грусть по ключевым словам
    elif any(word in text_lower for word in ['грустно', 'плохо', 'устал', 'печаль', 'горе']):
        result = "sad"
    # Проверка по score
    elif score > 0.45:
        result = "warm"
    elif score > 0.1:  # Уменьшил порог с 0.3 до 0.1
        result = "friendly"
    elif score < -0.45:
        result = "insult"
    elif score < -0.1:
        result = "angry"
    else:
        result = "neutral"

    logger.info(f"[Sentiment] Определен тон: {result} (score: {score})")
    return result
