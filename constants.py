"""
Stałe aplikacji Language Helper
"""

# OpenAI API
OPENAI_MODEL = "gpt-4o"
OPENAI_MAX_TOKENS = 1000
OPENAI_TEMPERATURE = 0.3
OPENAI_TTS_MODEL = "tts-1"
OPENAI_TTS_MAX_CHARS = 4000

# Qdrant Database
QDRANT_VECTOR_SIZE = 384
QDRANT_TIMEOUT = 60.0
QDRANT_DEFAULT_COLLECTION = "language_helper_history"

# Data Limits
DEFAULT_HISTORY_LIMIT = 20
MAX_HISTORY_LIMIT = 100
MAX_TEXT_LENGTH = 10000
MIN_TEXT_LENGTH = 3

# File Upload
MAX_FILE_SIZE_MB = 10
SUPPORTED_FILE_TYPES = ['txt', 'docx', 'pdf']

# Audio
MIN_AUDIO_SIZE_BYTES = 1000
AUDIO_FORMAT = "wav"

# UI
DEFAULT_REFRESH_INTERVAL = 30  # seconds

# Exercise Types
EXERCISE_TYPES = {
    "vocabulary": "📚 Słownictwo",
    "grammar": "📖 Gramatyka", 
    "translation": "🔄 Tłumaczenie"
}

# Language Mapping
LANGUAGE_VOICE_MAPPING = {
    "angielski": "alloy",
    "niemiecki": "onyx", 
    "francuski": "nova",
    "hiszpański": "echo",
    "włoski": "fable",
    "polski": "shimmer",
    "rosyjski": "onyx",
    "japoński": "nova",
    "koreański": "shimmer",
    "chiński": "alloy"
}

# Available Voices
AVAILABLE_VOICES = [
    ("alloy", "Alloy - neutralny"),
    ("echo", "Echo - męski"),
    ("fable", "Fable - młody"),
    ("onyx", "Onyx - poważny"),
    ("nova", "Nova - kobiecy"),
    ("shimmer", "Shimmer - przyjazny")
]

# Error Messages
ERROR_MESSAGES = {
    "no_api_key": "Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env",
    "text_too_short": "Tekst jest za krótki. Wprowadź co najmniej 3 znaki.",
    "text_too_long": f"Tekst jest za długi. Maksymalna długość to {MAX_TEXT_LENGTH} znaków.",
    "file_too_large": f"Plik jest za duży. Maksymalny rozmiar: {MAX_FILE_SIZE_MB}MB",
    "unsupported_format": "Nieobsługiwany format pliku",
    "audio_generation_failed": "Nie udało się wygenerować audio",
    "database_error": "Błąd połączenia z bazą danych"
}

# Success Messages
SUCCESS_MESSAGES = {
    "translation_saved": "✅ Tłumaczenie zakończone i zapisane w bazie danych!",
    "correction_saved": "✅ Poprawianie zakończone i zapisane w bazie danych!",
    "analysis_saved": "✅ Analiza zakończona i zapisana w bazie danych!",
    "exercise_saved": "✅ Ćwiczenie wygenerowane i zapisane w archiwum!",
    "tips_saved": "✅ Wskazówki wygenerowane i zapisane w archiwum!",
    "chat_saved": "✅ Odpowiedź wysłana!",
    "data_loaded": "✅ Historia została odświeżona z bazy danych!",
    "data_cleared": "✅ Historia została wyczyszczona z pamięci i bazy danych!"
}
