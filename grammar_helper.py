import openai
import os
from dotenv import load_dotenv
from typing import List, Dict
import instructor
from pydantic import BaseModel

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja OpenAI i instructor - tylko jeśli klucz API jest dostępny
client = None
instructor_client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = openai.OpenAI(api_key=api_key)
    instructor_client = instructor.patch(openai.OpenAI(api_key=api_key))

class VocabularyItem(BaseModel):
    """Model dla elementu słownictwa"""
    word: str
    translation: str
    part_of_speech: str
    example_sentence: str
    difficulty_level: str

class GrammarRule(BaseModel):
    """Model dla reguły gramatycznej"""
    rule_name: str
    explanation: str
    examples: List[str]
    difficulty_level: str

class LanguageAnalysis(BaseModel):
    """Model dla analizy językowej"""
    vocabulary_items: List[VocabularyItem]
    grammar_rules: List[GrammarRule]
    learning_tips: List[str]

def analyze_text(text: str, language: str = "angielski") -> LanguageAnalysis:
    """
    Analizuje tekst i zwraca słownictwo oraz reguły gramatyczne
    """
    if not instructor_client:
        return LanguageAnalysis(
            vocabulary_items=[],
            grammar_rules=[],
            learning_tips=["Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env"]
        )
    
    try:
        analysis = instructor_client.chat.completions.create(
            model="gpt-4o",
            response_model=LanguageAnalysis,
            messages=[
                {
                    "role": "system",
                    "content": f"Jesteś ekspertem w nauczaniu języka {language}. Przeanalizuj podany tekst i wyciągnij z niego ciekawe słownictwo oraz reguły gramatyczne, które mogą być przydatne do nauki. Wszystkie wyjaśnienia, tłumaczenia i wskazówki podawaj w języku polskim. Nazwy czasów gramatycznych, części mowy i reguł składni podawaj w języku {language} (np. Present Perfect, Past Continuous, Passive Voice)."
                },
                {
                    "role": "user",
                    "content": f"Przeanalizuj ten tekst ({language}): {text}"
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )
        return analysis
    except Exception as e:
        # Fallback - zwróć podstawową analizę
        return LanguageAnalysis(
            vocabulary_items=[],
            grammar_rules=[],
            learning_tips=[f"Błąd podczas analizy: {str(e)}"]
        )

def get_word_explanation(word: str, language: str = "angielski") -> Dict:
    """
    Zwraca szczegółowe wyjaśnienie słowa
    """
    if not client:
        return {
            "word": word,
            "translation": "Klucz API OpenAI nie jest skonfigurowany",
            "part_of_speech": "",
            "definition": "",
            "examples": [],
            "synonyms": [],
            "antonyms": []
        }
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Jesteś ekspertem w nauczaniu języka {language}. Podaj szczegółowe wyjaśnienie słowa w formacie JSON. Tłumaczenia i definicje podawaj w języku polskim. Nazwy części mowy podawaj w języku {language} (np. noun, verb, adjective)."
                },
                {
                    "role": "user",
                    "content": f"Wyjaśnij słowo '{word}' w języku {language}. Zwróć JSON z polami: word, translation, part_of_speech, definition, examples, synonyms, antonyms"
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        # Próba parsowania JSON z odpowiedzi
        import json
        try:
            return json.loads(response.choices[0].message.content)
        except:
            return {
                "word": word,
                "translation": "Błąd parsowania",
                "part_of_speech": "",
                "definition": "",
                "examples": [],
                "synonyms": [],
                "antonyms": []
            }
    except Exception as e:
        return {
            "word": word,
            "translation": f"Błąd: {str(e)}",
            "part_of_speech": "",
            "definition": "",
            "examples": [],
            "synonyms": [],
            "antonyms": []
        }
