"""
Menedżer cache dla aplikacji Language Helper
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from logger_config import log_debug, log_info

class CacheManager:
    """Menedżer cache z TTL (Time To Live)"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minut domyślnie
        """
        Inicjalizuje menedżer cache
        
        Args:
            default_ttl: Domyślny czas życia cache w sekundach
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        log_info(f"Cache manager zainicjalizowany z TTL: {default_ttl}s")
    
    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """
        Sprawdza czy wpis cache wygasł
        
        Args:
            cache_entry: Wpis cache do sprawdzenia
            
        Returns:
            bool: True jeśli wpis wygasł
        """
        if 'expires_at' not in cache_entry:
            return True
        
        return datetime.now() > cache_entry['expires_at']
    
    def get(self, key: str) -> Optional[Any]:
        """
        Pobiera wartość z cache
        
        Args:
            key: Klucz cache
            
        Returns:
            Wartość z cache lub None jeśli nie istnieje/wygasła
        """
        if key not in self.cache:
            log_debug(f"Cache miss: {key}")
            return None
        
        cache_entry = self.cache[key]
        
        if self._is_expired(cache_entry):
            log_debug(f"Cache expired: {key}")
            del self.cache[key]
            return None
        
        log_debug(f"Cache hit: {key}")
        return cache_entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Ustawia wartość w cache
        
        Args:
            key: Klucz cache
            value: Wartość do zapisania
            ttl: Czas życia w sekundach (opcjonalny)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        
        log_debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        Usuwa wpis z cache
        
        Args:
            key: Klucz do usunięcia
            
        Returns:
            bool: True jeśli wpis został usunięty
        """
        if key in self.cache:
            del self.cache[key]
            log_debug(f"Cache delete: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Czyści cały cache"""
        self.cache.clear()
        log_info("Cache cleared")
    
    def cleanup_expired(self) -> int:
        """
        Usuwa wygasłe wpisy z cache
        
        Returns:
            int: Liczba usuniętych wpisów
        """
        expired_keys = []
        
        for key, cache_entry in self.cache.items():
            if self._is_expired(cache_entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            log_debug(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki cache
        
        Returns:
            Dict ze statystykami cache
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if self._is_expired(entry))
        active_entries = total_entries - expired_entries
        
        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': expired_entries,
            'cache_size_mb': self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """
        Szacuje użycie pamięci przez cache
        
        Returns:
            float: Szacowane użycie pamięci w MB
        """
        import sys
        
        total_size = 0
        for key, value in self.cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(value)
        
        return round(total_size / (1024 * 1024), 2)

# Globalny menedżer cache
cache_manager = CacheManager(default_ttl=300)  # 5 minut

# Funkcje pomocnicze dla cache
def cache_translations(translations: List[Dict]) -> None:
    """Cache dla tłumaczeń"""
    cache_manager.set("translations", translations, ttl=600)  # 10 minut

def get_cached_translations() -> Optional[List[Dict]]:
    """Pobiera tłumaczenia z cache"""
    return cache_manager.get("translations")

def cache_corrections(corrections: List[Dict]) -> None:
    """Cache dla poprawek i analiz"""
    cache_manager.set("corrections", corrections, ttl=600)  # 10 minut

def get_cached_corrections() -> Optional[List[Dict]]:
    """Pobiera poprawki z cache"""
    return cache_manager.get("corrections")

def cache_chat_sessions(chat_sessions: List[Dict]) -> None:
    """Cache dla sesji czatu"""
    cache_manager.set("chat_sessions", chat_sessions, ttl=300)  # 5 minut

def get_cached_chat_sessions() -> Optional[List[Dict]]:
    """Pobiera sesje czatu z cache"""
    return cache_manager.get("chat_sessions")

def cache_tips_history(tips_history: List[Dict]) -> None:
    """Cache dla historii wskazówek"""
    cache_manager.set("tips_history", tips_history, ttl=300)  # 5 minut

def get_cached_tips_history() -> Optional[List[Dict]]:
    """Pobiera historię wskazówek z cache"""
    return cache_manager.get("tips_history")

def invalidate_cache(cache_type: str = None) -> None:
    """
    Unieważnia cache
    
    Args:
        cache_type: Typ cache do unieważnienia (opcjonalny)
    """
    if cache_type:
        cache_manager.delete(cache_type)
        log_info(f"Cache invalidated: {cache_type}")
    else:
        cache_manager.clear()
        log_info("All cache invalidated")
