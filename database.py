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
        if self.qdrant_api_key:
            self.client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
        else:
            self.client = QdrantClient(url=self.qdrant_url)
        
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
    
    def save_correction(self, input_text, output_text, explanation, language, mode="correction"):
        """Zapisuje poprawkę do bazy danych"""
        try:
            # Generowanie unikalnego ID
            point_id = str(uuid.uuid4())
            
            # Przygotowanie metadanych
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "input_text": input_text,
                "output_text": output_text,
                "explanation": explanation,
                "language": language,
                "mode": mode
            }
            
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
            
            print(f"✅ Zapisano poprawkę do bazy danych: {point_id}")
            return point_id
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania poprawki do bazy danych: {str(e)}")
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
        """Pobiera poprawki z bazy danych"""
        try:
            # Pobieranie punktów z bazy danych
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )[0]
            
            corrections = []
            for point in points:
                payload = point.payload
                if payload.get("mode") == "correction":
                    correction = {
                        "id": point.id,
                        "timestamp": datetime.fromisoformat(payload["timestamp"]),
                        "input": payload["input_text"],
                        "output": payload["output_text"],
                        "explanation": payload["explanation"],
                        "language": payload["language"],
                        "mode": "correction"
                    }
                    corrections.append(correction)
            
            # Sortowanie po timestamp (najnowsze pierwsze)
            corrections.sort(key=lambda x: x["timestamp"], reverse=True)
            return corrections
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania poprawek: {str(e)}")
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
