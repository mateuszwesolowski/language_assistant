import openai
import os
from dotenv import load_dotenv

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja OpenAI - tylko jeśli klucz API jest dostępny
client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key and api_key.strip():  # Sprawdź czy nie jest None i nie jest pustym stringiem
    try:
        client = openai.OpenAI(api_key=api_key)
    except Exception as e:
        print(f"Błąd podczas inicjalizacji klienta OpenAI: {e}")
        client = None

def correct_text(text, language="angielski"):
    """
    Funkcja do poprawiania błędów gramatycznych w tekście obcojęzycznym
    """
    if not client:
        return "Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Jesteś ekspertem w poprawianiu błędów gramatycznych w języku {language}. Popraw błędy w tekście i zwróć poprawioną wersję. Jeśli tekst jest już poprawny, zwróć go bez zmian. Odpowiadaj w języku polskim."
                },
                {
                    "role": "user",
                    "content": f"Popraw błędy w tym tekście ({language}): {text}"
                }
            ],
            max_tokens=1000,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Błąd podczas poprawiania tekstu: {str(e)}"

def get_correction_explanation(original_text, corrected_text, language="angielski"):
    """
    Funkcja do generowania wyjaśnienia poprawek
    """
    if not client:
        return "Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Jesteś nauczycielem języka {language}. Wyjaśnij jakie błędy zostały poprawione w tekście. Podaj krótkie i zrozumiałe wyjaśnienia w języku polskim. Używaj nazw gramatycznych w języku {language} (np. Present Perfect, Past Continuous), ale wyjaśnienia podawaj po polsku."
                },
                {
                    "role": "user",
                    "content": f"Oryginalny tekst: {original_text}\nPoprawiony tekst: {corrected_text}\nWyjaśnij jakie błędy zostały poprawione."
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Błąd podczas generowania wyjaśnienia: {str(e)}"
