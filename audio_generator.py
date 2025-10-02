import os
import tempfile
import base64
from pathlib import Path
from openai_client import get_global_openai_client
from logger_config import log_api_call, log_error, log_debug

# Konfiguracja OpenAI
client = get_global_openai_client()

def generate_audio(text: str, voice: str = "alloy", language: str = "en") -> bytes:
    """
    Generuje wersję audio tekstu używając OpenAI TTS
    """
    if not client:
        log_error("Klucz API OpenAI nie jest skonfigurowany")
        return None
    
    # Sprawdź długość tekstu (limit OpenAI TTS to ~4096 znaków)
    if len(text) > 4000:
        log_debug(f"Tekst za długi ({len(text)} znaków), przycinam do 4000")
        text = text[:4000] + "..."
    
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="wav",
            speed=1.0
        )
        
        # Sprawdź czy odpowiedź zawiera dane
        if not response.content:
            log_api_call("OpenAI TTS", False, "Brak danych audio w odpowiedzi")
            return None
        
        # Sprawdź rozmiar danych
        if len(response.content) < 1000:  # Minimalny rozmiar dla pliku MP3
            log_api_call("OpenAI TTS", False, f"Za mały rozmiar danych audio: {len(response.content)} bajtów")
            return None
        
        # Zapisz audio do pliku tymczasowego
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # Sprawdź czy plik został utworzony poprawnie
        if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
            log_error("Nie udało się utworzyć pliku audio")
            return None
        
        # Wczytaj plik i zwróć jako bytes
        with open(temp_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Usuń plik tymczasowy
        os.unlink(temp_file_path)
        
        log_api_call("OpenAI TTS", True, f"Audio wygenerowane: {len(audio_data)} bajtów")
        return audio_data
        
    except Exception as e:
        error_msg = str(e)
        log_api_call("OpenAI TTS", False, error_msg)
        
        # Sprawdź konkretne typy błędów
        if "quota" in error_msg.lower() or "billing" in error_msg.lower():
            log_error("Brak środków na koncie OpenAI")
        elif "invalid" in error_msg.lower() or "format" in error_msg.lower():
            log_error("Nieprawidłowy format tekstu")
        elif "rate" in error_msg.lower():
            log_error("Przekroczono limit zapytań")
        return None

def get_available_voices():
    """
    Zwraca listę dostępnych głosów
    """
    return [
        ("alloy", "Alloy - neutralny"),
        ("echo", "Echo - męski"),
        ("fable", "Fable - młody"),
        ("onyx", "Onyx - poważny"),
        ("nova", "Nova - kobiecy"),
        ("shimmer", "Shimmer - przyjazny")
    ]

def get_voice_for_language(language: str) -> str:
    """
    Zwraca odpowiedni głos dla danego języka
    """
    voice_mapping = {
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
    
    return voice_mapping.get(language, "alloy")

def save_audio_file(audio_data: bytes, filename: str = "audio.mp3") -> str:
    """
    Zapisuje audio do pliku i zwraca ścieżkę
    """
    try:
        # Utwórz katalog audio jeśli nie istnieje
        audio_dir = Path("audio_files")
        audio_dir.mkdir(exist_ok=True)
        
        # Zapisz plik
        file_path = audio_dir / filename
        with open(file_path, 'wb') as f:
            f.write(audio_data)
        
        return str(file_path)
    except Exception as e:
        log_error(f"Błąd podczas zapisywania pliku audio: {str(e)}")
        return None
