"""
Walidatory dla aplikacji Language Helper
"""

from constants import (
    MIN_TEXT_LENGTH, 
    MAX_TEXT_LENGTH, 
    MAX_FILE_SIZE_MB,
    SUPPORTED_FILE_TYPES,
    ERROR_MESSAGES
)

def validate_text_input(text: str) -> tuple[bool, str]:
    """
    Waliduje tekst wprowadzony przez użytkownika
    
    Args:
        text: Tekst do walidacji
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Wprowadź tekst do przetworzenia."
    
    text = text.strip()
    
    if len(text) < MIN_TEXT_LENGTH:
        return False, ERROR_MESSAGES["text_too_short"]
    
    if len(text) > MAX_TEXT_LENGTH:
        return False, ERROR_MESSAGES["text_too_long"]
    
    return True, ""

def validate_file_upload(uploaded_file) -> tuple[bool, str]:
    """
    Waliduje plik przesłany przez użytkownika
    
    Args:
        uploaded_file: Plik przesłany przez Streamlit
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if uploaded_file is None:
        return False, "Nie wybrano pliku"
    
    # Sprawdź rozmiar pliku
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        return False, ERROR_MESSAGES["file_too_large"]
    
    # Sprawdź typ pliku
    file_extension = uploaded_file.name.lower().split('.')[-1]
    if file_extension not in SUPPORTED_FILE_TYPES:
        return False, f"{ERROR_MESSAGES['unsupported_format']}: {file_extension}"
    
    return True, ""

def validate_language(language: str) -> tuple[bool, str]:
    """
    Waliduje wybrany język
    
    Args:
        language: Język do walidacji
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not language or not language.strip():
        return False, "Wybierz język"
    
    # Lista obsługiwanych języków
    supported_languages = [
        "angielski", "niemiecki", "francuski", "hiszpański", 
        "włoski", "rosyjski", "japoński", "koreański", "chiński"
    ]
    
    if language not in supported_languages:
        return False, f"Nieobsługiwany język: {language}"
    
    return True, ""

def sanitize_text(text: str) -> str:
    """
    Sanityzuje tekst wprowadzony przez użytkownika
    
    Args:
        text: Tekst do sanityzacji
        
    Returns:
        str: Oczyszczony tekst
    """
    if not text:
        return ""
    
    # Usuń nadmiarowe białe znaki
    text = " ".join(text.split())
    
    # Usuń potencjalnie niebezpieczne znaki
    dangerous_chars = ['<', '>', '&', '"', "'"]
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()

def validate_exercise_type(exercise_type: str) -> tuple[bool, str]:
    """
    Waliduje typ ćwiczenia
    
    Args:
        exercise_type: Typ ćwiczenia do walidacji
        
    Returns:
        tuple: (is_valid, error_message)
    """
    valid_types = ["vocabulary", "grammar", "translation"]
    
    if exercise_type not in valid_types:
        return False, f"Nieznany typ ćwiczenia: {exercise_type}"
    
    return True, ""
