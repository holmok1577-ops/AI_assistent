from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()

def detect_tone(text: str):
    logger.info(f"[Sentiment] Определение тона для сообщения: {text[:50]}...")
    score = analyzer.polarity_scores(text)["compound"]
    text_lower = text.lower()

    # Проверка на мат по ключевым словам
    profanity_keywords = ['бля', 'блять', 'хуй', 'пизда', 'ебать', 'ебаный', 'пидор', 'сука', 'нахер', 'нахрен', 'блядь']
    if any(keyword in text_lower for keyword in profanity_keywords):
        result = "profane"
    # Проверка на флирт по ключевым словам
    elif any(keyword in text_lower for keyword in ['люблю', 'нравишься', 'красивая', 'милая', 'обнимаю', 'целую', 'соскучился', 'хочу тебя']):
        result = "flirty"
    # Проверка на грусть по ключевым словам
    elif any(word in text_lower for word in ['грустно', 'плохо', 'устал', 'печаль', 'горе']):
        result = "sad"
    # Проверка по score
    elif score > 0.1:  # Уменьшил порог с 0.3 до 0.1
        result = "friendly"
    elif score < -0.1:
        result = "angry"
    else:
        result = "neutral"

    logger.info(f"[Sentiment] Определен тон: {result} (score: {score})")
    return result
