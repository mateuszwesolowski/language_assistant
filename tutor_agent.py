import openai
from datetime import datetime
from typing import List, Dict, Any, Optional
from database import LanguageHelperDB

class TutorAgent:
    def __init__(self, client: openai.OpenAI, db: LanguageHelperDB):
        self.client = client
        self.db = db
    
    def get_user_history_summary(self, target_language: str) -> str:
        """Pobiera podsumowanie historii użytkownika dla danego języka"""
        try:
            # Pobierz tłumaczenia
            translations = self.db.get_translations(limit=50)
            user_translations = [t for t in translations if t.get('target_language') == target_language]
            
            # Pobierz poprawki i analizy
            corrections = self.db.get_corrections(limit=50)
            user_corrections = [c for c in corrections if c.get('language') == target_language]
            
            # Analizy
            user_analyses = [c for c in user_corrections if c.get('mode') == 'analysis']
            
            # Słownictwo z analiz
            vocabulary_words = []
            for analysis in user_analyses:
                if 'analysis' in analysis and analysis['analysis']:
                    if hasattr(analysis['analysis'], 'vocabulary_items'):
                        for vocab in analysis['analysis'].vocabulary_items:
                            vocabulary_words.append({
                                'word': vocab.word,
                                'translation': vocab.translation,
                                'part_of_speech': vocab.part_of_speech,
                                'difficulty': vocab.difficulty_level
                            })
            
            # Błędy z poprawek
            common_errors = []
            for correction in user_corrections:
                if correction.get('mode') == 'correction' and correction.get('explanation'):
                    common_errors.append(correction['explanation'])
            
            summary = f"""
            HISTORIA NAUKI - JĘZYK {target_language.upper()}:
            
            Liczba tłumaczeń: {len(user_translations)}
            Liczba poprawek: {len([c for c in user_corrections if c.get('mode') == 'correction'])}
            Liczba analiz: {len(user_analyses)}
            
            POZNAWE SŁOWA ({len(vocabulary_words)}):
            {chr(10).join([f"- {v['word']} ({v['translation']}) - {v['part_of_speech']} - poziom: {v['difficulty']}" for v in vocabulary_words[:20]])}
            
            OSTATNIE BŁĘDY:
            {chr(10).join([f"- {error[:100]}..." for error in common_errors[:5]])}
            """
            
            return summary
        except Exception as e:
            return f"Błąd podczas pobierania historii: {str(e)}"
    
    def generate_exercise(self, target_language: str, exercise_type: str = "vocabulary") -> Dict[str, Any]:
        """Generuje ćwiczenie na podstawie historii użytkownika"""
        if not self.client:
            return {"error": "Klucz API OpenAI nie jest skonfigurowany"}
        
        try:
            history_summary = self.get_user_history_summary(target_language)
            
            if exercise_type == "vocabulary":
                system_prompt = f"""Jesteś korepetytorem języka {target_language}. Na podstawie historii nauki użytkownika, 
                stwórz ćwiczenie ze słownictwa. Użyj słów, które użytkownik już poznał.
                
                HISTORIA UŻYTKOWNIKA:
                {history_summary}
                
                Stwórz ćwiczenie w formacie JSON:
                {{
                    "type": "vocabulary",
                    "title": "Tytuł ćwiczenia",
                    "description": "Opis ćwiczenia",
                    "question": "Pytanie do użytkownika",
                    "correct_answer": "Poprawna odpowiedź",
                    "options": ["opcja1", "opcja2", "opcja3", "opcja4"],
                    "explanation": "Wyjaśnienie po polsku",
                    "difficulty": "easy/medium/hard",
                    "hint": "Podpowiedź"
                }}
                
                Odpowiedz TYLKO w formacie JSON, bez żadnych dodatkowych komentarzy, markdown lub innych formatowań. 
                Odpowiedź musi zaczynać się od {{ i kończyć na }}."""
            
            elif exercise_type == "grammar":
                system_prompt = f"""Jesteś korepetytorem języka {target_language}. Na podstawie historii nauki użytkownika, 
                stwórz ćwiczenie gramatyczne. Uwzględnij błędy, które użytkownik popełniał.
                
                HISTORIA UŻYTKOWNIKA:
                {history_summary}
                
                Stwórz ćwiczenie w formacie JSON:
                {{
                    "type": "grammar",
                    "title": "Tytuł ćwiczenia",
                    "description": "Opis ćwiczenia",
                    "question": "Zdanie z błędem do poprawienia",
                    "correct_answer": "Poprawione zdanie",
                    "explanation": "Wyjaśnienie błędu po polsku",
                    "grammar_rule": "Nazwa reguły gramatycznej",
                    "difficulty": "easy/medium/hard",
                    "hint": "Podpowiedź"
                }}
                
                Odpowiedz TYLKO w formacie JSON, bez żadnych dodatkowych komentarzy, markdown lub innych formatowań. 
                Odpowiedź musi zaczynać się od {{ i kończyć na }}."""
            
            elif exercise_type == "translation":
                system_prompt = f"""Jesteś korepetytorem języka {target_language}. Na podstawie historii nauki użytkownika, 
                stwórz ćwiczenie tłumaczeniowe. Użyj słownictwa i struktur, które użytkownik już poznał.
                
                HISTORIA UŻYTKOWNIKA:
                {history_summary}
                
                Stwórz ćwiczenie w formacie JSON:
                {{
                    "type": "translation",
                    "title": "Tytuł ćwiczenia",
                    "description": "Opis ćwiczenia",
                    "question": "Zdanie do przetłumaczenia z polskiego na {target_language}",
                    "correct_answer": "Poprawne tłumaczenie",
                    "explanation": "Wyjaśnienie trudnych elementów po polsku",
                    "key_vocabulary": ["słowo1", "słowo2"],
                    "difficulty": "easy/medium/hard",
                    "hint": "Podpowiedź"
                }}
                
                Odpowiedz TYLKO w formacie JSON, bez żadnych dodatkowych komentarzy, markdown lub innych formatowań. 
                Odpowiedź musi zaczynać się od {{ i kończyć na }}."""
            
            else:
                return {"error": "Nieznany typ ćwiczenia"}
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            import json
            try:
                content = response.choices[0].message.content.strip()
                print(f"DEBUG: Raw AI response: {content}")
                
                # Usuń ewentualne markdown formatting
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                print(f"DEBUG: Cleaned content: {content}")
                
                # Sprawdź czy content zaczyna się i kończy na nawiasach klamrowych
                if not (content.startswith('{') and content.endswith('}')):
                    return {"error": "Odpowiedź AI nie jest w formacie JSON"}
                
                exercise_data = json.loads(content)
                exercise_data['timestamp'] = datetime.now().isoformat()  # Konwertuj na string
                return exercise_data
            except json.JSONDecodeError as e:
                print(f"DEBUG: JSON parsing error: {e}")
                print(f"DEBUG: Raw response: {response.choices[0].message.content}")
                return {"error": f"Błąd parsowania odpowiedzi AI: {str(e)}"}
                
        except Exception as e:
            return {"error": f"Błąd podczas generowania ćwiczenia: {str(e)}"}
    
    def get_learning_tips(self, target_language: str) -> List[str]:
        """Generuje wskazówki do nauki na podstawie historii użytkownika"""
        if not self.client:
            return ["Klucz API OpenAI nie jest skonfigurowany"]
        
        try:
            history_summary = self.get_user_history_summary(target_language)
            
            system_prompt = f"""Jesteś korepetytorem języka {target_language}. Na podstawie historii nauki użytkownika, 
            wygeneruj 3-5 praktycznych wskazówek do dalszej nauki. Wskazówki powinny być konkretne i oparte na tym, 
            co użytkownik już poznał i jakie błędy popełniał.
            
            HISTORIA UŻYTKOWNIKA:
            {history_summary}
            
            Odpowiedz w formacie listy, każda wskazówka w nowej linii zaczynając od "• ".
            Wskazówki powinny być po polsku i konkretne."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            tips = response.choices[0].message.content.strip().split('\n')
            tips = [tip.strip() for tip in tips if tip.strip().startswith('• ')]
            return tips if tips else ["Brak danych do wygenerowania wskazówek"]
            
        except Exception as e:
            return [f"Błąd podczas generowania wskazówek: {str(e)}"]
    
    def answer_question_with_context(self, question: str, target_language: str, context: str = "") -> str:
        """Odpowiada na pytania użytkownika z kontekstem z innych sekcji"""
        if not self.client:
            return "Klucz API OpenAI nie jest skonfigurowany"
        
        try:
            history_summary = self.get_user_history_summary(target_language)
            
            system_prompt = f"""Jesteś korepetytorem języka {target_language}. Odpowiadaj na pytania użytkownika w sposób przyjazny i pomocny.
            
            HISTORIA NAUKI UŻYTKOWNIKA:
            {history_summary}
            
            {context}
            
            Odpowiadaj po polsku, ale używaj przykładów w języku {target_language}. Bądź pomocny i motywujący."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Błąd podczas odpowiadania na pytanie: {str(e)}"
    
    def answer_question(self, question: str, target_language: str) -> str:
        """Odpowiada na pytania użytkownika dotyczące języka"""
        if not self.client:
            return "Klucz API OpenAI nie jest skonfigurowany"
        
        try:
            history_summary = self.get_user_history_summary(target_language)
            
            system_prompt = f"""Jesteś korepetytorem języka {target_language}. Odpowiadaj na pytania użytkownika 
            w sposób przyjazny i pomocny. Używaj języka polskiego w wyjaśnieniach, ale podawaj przykłady w {target_language}.
            
            HISTORIA NAUKI UŻYTKOWNIKA:
            {history_summary}
            
            Odpowiadaj w sposób:
            1. Krótko i zrozumiale
            2. Z przykładami
            3. Uwzględniając poziom użytkownika
            4. Po polsku z przykładami w {target_language}"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Błąd podczas odpowiadania na pytanie: {str(e)}"
