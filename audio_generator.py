import openai
import os
from dotenv import load_dotenv
import tempfile
import base64
from pathlib import Path

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja OpenAI - tylko jeśli klucz API jest dostępny
client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = openai.OpenAI(api_key=api_key)

def generate_audio(text: str, voice: str = "alloy", language: str = "en") -> bytes:
    """
    Generuje wersję audio tekstu używając OpenAI TTS
    """
    if not client:
        print("Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env")
        return None
    
    # Sprawdź długość tekstu (limit OpenAI TTS to ~4096 znaków)
    if len(text) > 4000:
        print(f"Tekst jest za długi ({len(text)} znaków). Maksymalna długość to 4000 znaków.")
        text = text[:4000] + "..."
        print(f"Przycięto do {len(text)} znaków.")
    
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
            print("Błąd: Brak danych audio w odpowiedzi")
            return None
        
        # Sprawdź rozmiar danych
        if len(response.content) < 1000:  # Minimalny rozmiar dla pliku MP3
            print(f"Błąd: Za mały rozmiar danych audio: {len(response.content)} bajtów")
            return None
        
        # Zapisz audio do pliku tymczasowego
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        # Sprawdź czy plik został utworzony poprawnie
        if not os.path.exists(temp_file_path) or os.path.getsize(temp_file_path) == 0:
            print("Błąd: Nie udało się utworzyć pliku audio")
            return None
        
        # Wczytaj plik i zwróć jako bytes
        with open(temp_file_path, 'rb') as f:
            audio_data = f.read()
        
        # Usuń plik tymczasowy
        os.unlink(temp_file_path)
        
        print(f"✅ Audio wygenerowane pomyślnie: {len(audio_data)} bajtów")
        return audio_data
        
    except Exception as e:
        print(f"Błąd podczas generowania audio: {str(e)}")
        # Sprawdź konkretne typy błędów
        if "quota" in str(e).lower() or "billing" in str(e).lower():
            print("Błąd: Brak środków na koncie OpenAI")
        elif "invalid" in str(e).lower() or "format" in str(e).lower():
            print("Błąd: Nieprawidłowy format tekstu")
        elif "rate" in str(e).lower():
            print("Błąd: Przekroczono limit zapytań")
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
        print(f"Błąd podczas zapisywania pliku audio: {str(e)}")
        return None
