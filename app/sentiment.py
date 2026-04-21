from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logger = logging.getLogger(__name__)

analyzer = SentimentIntensityAnalyzer()

def detect_tone(text: str):
    logger.info(f"[Sentiment] Определение тона для сообщения: {text[:50]}...")
    score = analyzer.polarity_scores(text)["compound"]

    if score > 0.3:
        result = "friendly"
    elif score < -0.3:
        result = "angry"
    else:
        result = "neutral"

    logger.info(f"[Sentiment] Определен тон: {result} (score: {score})")
    return result
