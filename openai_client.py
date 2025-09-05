"""
Centralny moduł do obsługi klienta OpenAI
"""

import os
import openai
from dotenv import load_dotenv
from typing import Optional
from logger_config import log_openai_init

# Ładowanie zmiennych środowiskowych
load_dotenv()

def get_openai_client() -> Optional[openai.OpenAI]:
    """
    Zwraca skonfigurowanego klienta OpenAI lub None jeśli klucz API nie jest dostępny
    
    Returns:
        Optional[openai.OpenAI]: Klient OpenAI lub None
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or not api_key.strip():
        log_openai_init(False, "Brak klucza API OpenAI w zmiennych środowiskowych")
        return None
    
    try:
        client = openai.OpenAI(api_key=api_key)
        log_openai_init(True)
        return client
    except Exception as e:
        log_openai_init(False, str(e))
        return None

def get_instructor_client() -> Optional[openai.OpenAI]:
    """
    Zwraca skonfigurowanego klienta OpenAI z patchem instructor lub None
    
    Returns:
        Optional[openai.OpenAI]: Klient OpenAI z instructor lub None
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or not api_key.strip():
        log_openai_init(False, "Brak klucza API OpenAI w zmiennych środowiskowych")
        return None
    
    try:
        import instructor
        client = instructor.patch(openai.OpenAI(api_key=api_key))
        log_openai_init(True, "z instructor")
        return client
    except Exception as e:
        log_openai_init(False, f"z instructor: {str(e)}")
        return None

# Globalne instancje klientów
_openai_client = None
_instructor_client = None

def get_global_openai_client() -> Optional[openai.OpenAI]:
    """
    Zwraca globalną instancję klienta OpenAI (singleton)
    
    Returns:
        Optional[openai.OpenAI]: Globalny klient OpenAI lub None
    """
    global _openai_client
    if _openai_client is None:
        _openai_client = get_openai_client()
    return _openai_client

def get_global_instructor_client() -> Optional[openai.OpenAI]:
    """
    Zwraca globalną instancję klienta OpenAI z instructor (singleton)
    
    Returns:
        Optional[openai.OpenAI]: Globalny klient OpenAI z instructor lub None
    """
    global _instructor_client
    if _instructor_client is None:
        _instructor_client = get_instructor_client()
    return _instructor_client
