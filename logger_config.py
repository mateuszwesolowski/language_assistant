"""
Konfiguracja systemu logowania dla aplikacji Language Helper
"""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name: str = "language_helper", level: str = "INFO") -> logging.Logger:
    """
    Konfiguruje logger dla aplikacji
    
    Args:
        name: Nazwa loggera
        level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Skonfigurowany logger
    """
    # Utwórz logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Unikaj duplikowania handlerów
    if logger.handlers:
        return logger
    
    # Utwórz format logów
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler dla konsoli
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler dla pliku (tylko w trybie deweloperskim)
    if os.getenv("ENVIRONMENT", "production") == "development":
        # Utwórz katalog logs jeśli nie istnieje
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Plik logów z datą
        log_file = logs_dir / f"language_helper_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Globalny logger
logger = setup_logger()

# Funkcje pomocnicze dla różnych poziomów logowania
def log_info(message: str, **kwargs):
    """Loguje wiadomość na poziomie INFO"""
    logger.info(message, **kwargs)

def log_debug(message: str, **kwargs):
    """Loguje wiadomość na poziomie DEBUG"""
    logger.debug(message, **kwargs)

def log_warning(message: str, **kwargs):
    """Loguje wiadomość na poziomie WARNING"""
    logger.warning(message, **kwargs)

def log_error(message: str, **kwargs):
    """Loguje wiadomość na poziomie ERROR"""
    logger.error(message, **kwargs)

def log_critical(message: str, **kwargs):
    """Loguje wiadomość na poziomie CRITICAL"""
    logger.critical(message, **kwargs)

# Funkcje specjalne dla różnych komponentów
def log_openai_init(success: bool, error: str = None):
    """Loguje inicjalizację klienta OpenAI"""
    if success:
        log_info("✅ Klient OpenAI zainicjalizowany poprawnie")
    else:
        log_error(f"❌ Błąd podczas inicjalizacji klienta OpenAI: {error}")

def log_database_operation(operation: str, success: bool, details: str = None):
    """Loguje operacje na bazie danych"""
    if success:
        log_info(f"✅ {operation} - {details or 'operacja zakończona pomyślnie'}")
    else:
        log_error(f"❌ Błąd podczas {operation}: {details}")

def log_user_action(action: str, details: str = None):
    """Loguje akcje użytkownika"""
    log_info(f"👤 Akcja użytkownika: {action} - {details or ''}")

def log_api_call(service: str, success: bool, details: str = None):
    """Loguje wywołania API"""
    if success:
        log_info(f"🌐 API {service} - {details or 'wywołanie zakończone pomyślnie'}")
    else:
        log_error(f"🌐 Błąd API {service}: {details}")
