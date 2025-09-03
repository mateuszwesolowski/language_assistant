import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from datetime import datetime
import json
import uuid

# Ładowanie zmiennych środowiskowych
load_dotenv()

class LanguageHelperDB:
    """Klasa do obsługi bazy danych Qdrant dla aplikacji Language Helper"""
    
    def __init__(self):
        """Inicjalizacja połączenia z bazą danych"""
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "language_helper_history")
        
        # Inicjalizacja klienta Qdrant
        try:
            if self.qdrant_api_key:
                self.client = QdrantClient(
                    url=self.qdrant_url, 
                    api_key=self.qdrant_api_key,
                    timeout=60.0  # Dodaj timeout
                )
            else:
                self.client = QdrantClient(
                    url=self.qdrant_url,
                    timeout=60.0  # Dodaj timeout
                )
            print(f"✅ Połączenie z Qdrant: {self.qdrant_url}")
        except Exception as e:
            print(f"❌ Błąd podczas łączenia z Qdrant: {str(e)}")
            self.client = None
        
        # Utworzenie kolekcji jeśli nie istnieje
        self._create_collection_if_not_exists()
    
    def _create_collection_if_not_exists(self):
        """Tworzy kolekcję w Qdrant jeśli nie istnieje"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                # Utworzenie kolekcji z wektorami 384-wymiarowymi (dla embeddings)
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                print(f"✅ Utworzono kolekcję: {self.collection_name}")
            else:
                print(f"✅ Kolekcja {self.collection_name} już istnieje")
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia kolekcji: {str(e)}")
    
    def save_translation(self, input_text, output_text, target_language, mode="translation", audio_data=None, voice=None):
        """Zapisuje tłumaczenie do bazy danych"""
        try:
            # Generowanie unikalnego ID
            point_id = str(uuid.uuid4())
            
            # Przygotowanie metadanych
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "input_text": input_text,
                "output_text": output_text,
                "target_language": target_language,
                "mode": mode,
                "voice": voice,
                "has_audio": audio_data is not None
            }
            
            # Jeśli jest audio, zapisz je jako base64
            if audio_data:
                import base64
                metadata["audio_data"] = base64.b64encode(audio_data).decode('utf-8')
            
            # Tworzenie punktu w bazie danych
            point = PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Placeholder vector
                payload=metadata
            )
            
            # Zapisanie do bazy danych
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✅ Zapisano tłumaczenie do bazy danych: {point_id}")
            return point_id
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania do bazy danych: {str(e)}")
            return None
    
    def save_correction(self, input_text, output_text, explanation, language, mode="correction", analysis_data=None):
        """Zapisuje poprawkę lub analizę do bazy danych"""
        try:
            # Generowanie unikalnego ID
            point_id = str(uuid.uuid4())
            
            # Przygotowanie metadanych
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "input_text": input_text,
                "output_text": output_text,
                "language": language,
                "mode": mode
            }
            
            # Dodaj specyficzne pola dla każdego trybu
            if mode == "correction":
                metadata["explanation"] = explanation
            elif mode == "analysis" and analysis_data:
                # Serializuj dane analizy jako JSON
                import json
                # Konwertuj obiekt Pydantic na słownik
                analysis_dict = analysis_data.dict() if hasattr(analysis_data, 'dict') else analysis_data
                metadata["analysis_data"] = json.dumps(analysis_dict)
            elif mode == "exercise" and analysis_data:  # analysis_data zawiera dane ćwiczenia
                # Serializuj dane ćwiczenia jako JSON
                import json
                metadata["exercise_data"] = json.dumps(analysis_data)
            
            # Tworzenie punktu w bazie danych
            point = PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Placeholder vector
                payload=metadata
            )
            
            # Zapisanie do bazy danych
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✅ Zapisano {mode} do bazy danych: {point_id}")
            if mode == "analysis":
                print(f"✅ Analiza została zapisana w formacie JSON zamiast pickle")
            return point_id
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania {mode} do bazy danych: {str(e)}")
            return None
    
    def save_chat_session(self, messages: list, language: str, context: str = ""):
        """Zapisuje sesję czatu do bazy danych"""
        try:
            # Generowanie unikalnego ID
            point_id = str(uuid.uuid4())
            
            # Przygotowanie metadanych
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "language": language,
                "context": context,
                "mode": "chat_session"
            }
            
            # Konwertuj wiadomości na string
            chat_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            # Tworzenie punktu w bazie danych
            point = PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Placeholder vector
                payload={
                    **metadata,
                    "chat_text": chat_text,
                    "message_count": len(messages)
                }
            )
            
            # Zapisanie do bazy danych
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✅ Zapisano sesję czatu do bazy danych: {point_id}")
            return point_id
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania sesji czatu do bazy danych: {str(e)}")
            return None
    
    def save_learning_tips(self, tips: list, language: str):
        """Zapisuje wskazówki do nauki do bazy danych"""
        try:
            # Generowanie unikalnego ID
            point_id = str(uuid.uuid4())
            
            # Przygotowanie metadanych
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "language": language,
                "mode": "learning_tips"
            }
            
            tips_text = "\n".join(tips)
            
            # Tworzenie punktu w bazie danych
            point = PointStruct(
                id=point_id,
                vector=[0.0] * 384,  # Placeholder vector
                payload={
                    **metadata,
                    "tips_text": tips_text,
                    "tips_count": len(tips)
                }
            )
            
            # Zapisanie do bazy danych
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            print(f"✅ Zapisano wskazówki do bazy danych: {point_id}")
            return point_id
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania wskazówek do bazy danych: {str(e)}")
            return None
    
    def get_translations(self, limit=50):
        """Pobiera tłumaczenia z bazy danych"""
        try:
            # Pobieranie punktów z bazy danych
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]
            
            translations = []
            for point in points:
                payload = point.payload
                if payload.get("mode") == "translation":
                    # Konwersja audio z base64 jeśli istnieje
                    audio_data = None
                    if payload.get("has_audio") and "audio_data" in payload:
                        import base64
                        audio_data = base64.b64decode(payload["audio_data"])
                    
                    translation = {
                        "id": point.id,
                        "timestamp": datetime.fromisoformat(payload["timestamp"]),
                        "input": payload["input_text"],
                        "output": payload["output_text"],
                        "target_language": payload["target_language"],
                        "mode": "translation",
                        "audio_data": audio_data,
                        "voice": payload.get("voice")
                    }
                    translations.append(translation)
            
            # Sortowanie po timestamp (najnowsze pierwsze)
            translations.sort(key=lambda x: x["timestamp"], reverse=True)
            return translations
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania tłumaczeń: {str(e)}")
            return []
    
    def get_corrections(self, limit=50):
        """Pobiera poprawki i analizy z bazy danych"""
        try:
            # Pobieranie punktów z bazy danych - zwiększamy limit żeby złapać nowe ćwiczenia
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,  # Zwiększamy z 20 na 100
                with_payload=True,
                with_vectors=False
            )[0]
            
            corrections = []
            for point in points:
                payload = point.payload
                if payload.get("mode") in ["correction", "analysis", "exercise"]:
                    # Podstawowe dane
                    item = {
                        "id": point.id,
                        "timestamp": datetime.fromisoformat(payload["timestamp"]),
                        "input": payload["input_text"],
                        "output": payload["output_text"],
                        "language": payload["language"],
                        "mode": payload["mode"]
                    }
                    
                    # Dodaj specyficzne pola dla każdego trybu
                    if payload.get("mode") == "correction":
                        item["explanation"] = payload["explanation"]
                    elif payload.get("mode") == "analysis":
                        # Dla analiz, deserializuj dane z JSON
                        if "analysis_data" in payload:
                            import json
                            try:
                                analysis_dict = json.loads(payload["analysis_data"])
                                # Rekonstruuj obiekt analizy z słownika
                                from types import SimpleNamespace
                                
                                # Rekonstruuj vocabulary_items
                                vocabulary_items = []
                                for vocab_dict in analysis_dict.get('vocabulary_items', []):
                                    vocab_obj = SimpleNamespace(**vocab_dict)
                                    vocabulary_items.append(vocab_obj)
                                
                                # Rekonstruuj grammar_rules
                                grammar_rules = []
                                for rule_dict in analysis_dict.get('grammar_rules', []):
                                    rule_obj = SimpleNamespace(**rule_dict)
                                    grammar_rules.append(rule_obj)
                                
                                # Rekonstruuj cały obiekt analizy
                                analysis_obj = SimpleNamespace(
                                    vocabulary_items=vocabulary_items,
                                    grammar_rules=grammar_rules,
                                    learning_tips=analysis_dict.get('learning_tips', [])
                                )
                                item["analysis"] = analysis_obj
                            except Exception as e:
                                print(f"❌ Błąd deserializacji analizy: {str(e)}")
                                item["analysis"] = None
                    elif payload.get("mode") == "exercise":
                        # Dla ćwiczeń, deserializuj dane z JSON
                        if "exercise_data" in payload:
                            import json
                            try:
                                exercise_dict = json.loads(payload["exercise_data"])
                                item["exercise"] = exercise_dict
                            except Exception as e:
                                print(f"❌ Błąd deserializacji ćwiczenia: {str(e)}")
                                item["exercise"] = None
                    
                    corrections.append(item)
            
            # Sortowanie po timestamp (najnowsze pierwsze)
            corrections.sort(key=lambda x: x["timestamp"], reverse=True)
            return corrections
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania poprawek i analiz: {str(e)}")
            return []
    
    def get_chat_sessions(self, limit=20):
        """Pobiera sesje czatu z bazy danych"""
        try:
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]
            
            chat_sessions = []
            for point in points:
                payload = point.payload
                if payload.get("mode") == "chat_session":
                    chat_session = {
                        "id": point.id,
                        "timestamp": datetime.fromisoformat(payload["timestamp"]),
                        "language": payload["language"],
                        "context": payload.get("context", ""),
                        "chat_text": payload["chat_text"],
                        "message_count": payload["message_count"],
                        "mode": "chat_session"
                    }
                    chat_sessions.append(chat_session)
            
            # Sortowanie po timestamp (najnowsze pierwsze)
            chat_sessions.sort(key=lambda x: x["timestamp"], reverse=True)
            return chat_sessions
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania sesji czatu: {str(e)}")
            return []
    
    def get_learning_tips_history(self, limit=20):
        """Pobiera historię wskazówek do nauki z bazy danych"""
        try:
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]
            
            tips_history = []
            for point in points:
                payload = point.payload
                
                if payload.get("mode") == "learning_tips":
                    tips_history_item = {
                        "id": point.id,
                        "timestamp": datetime.fromisoformat(payload["timestamp"]),
                        "language": payload["language"],
                        "tips_text": payload["tips_text"],
                        "tips_count": payload["tips_count"],
                        "mode": "learning_tips"
                    }
                    tips_history.append(tips_history_item)
            
            # Sortowanie po timestamp (najnowsze pierwsze)
            tips_history.sort(key=lambda x: x["timestamp"], reverse=True)
            return tips_history
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania historii wskazówek: {str(e)}")
            return []
    
    def delete_item(self, item_id):
        """Usuwa element z bazy danych"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[item_id]
            )
            print(f"✅ Usunięto element z bazy danych: {item_id}")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas usuwania elementu: {str(e)}")
            return False
    
    def clear_all(self):
        """Usuwa wszystkie elementy z bazy danych"""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector="all"
            )
            print(f"✅ Wyczyszczono całą bazę danych")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas czyszczenia bazy danych: {str(e)}")
            return False
    
    def get_stats(self):
        """Zwraca statystyki bazy danych"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "total_points": info.points_count,
                "collection_name": self.collection_name,
                "status": "connected"
            }
        except Exception as e:
            return {
                "total_points": 0,
                "collection_name": self.collection_name,
                "status": f"error: {str(e)}"
            }
