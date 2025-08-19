import os
import streamlit as st
from docx import Document
import PyPDF2
import io

def extract_text_from_file(uploaded_file):
    """
    Wyciąga tekst z różnych formatów plików
    """
    if uploaded_file is None:
        return None, "Nie wybrano pliku"
    
    file_extension = uploaded_file.name.lower().split('.')[-1]
    
    try:
        if file_extension == 'txt':
            # Obsługa plików TXT
            content = uploaded_file.read()
            # Próba dekodowania z różnych kodowań
            for encoding in ['utf-8', 'cp1250', 'iso-8859-2', 'latin-1']:
                try:
                    text = content.decode(encoding)
                    return text, None
                except UnicodeDecodeError:
                    continue
            return None, "Nie udało się odczytać pliku TXT - problem z kodowaniem"
        
        elif file_extension == 'docx':
            # Obsługa plików DOCX
            doc = Document(uploaded_file)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return '\n'.join(text), None
        
        elif file_extension == 'pdf':
            # Obsługa plików PDF
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text.strip():
                    text.append(page_text)
            return '\n'.join(text), None
        
        else:
            return None, f"Nieobsługiwany format pliku: {file_extension}"
    
    except Exception as e:
        return None, f"Błąd podczas odczytywania pliku: {str(e)}"

def validate_file_size(uploaded_file, max_size_mb=10):
    """
    Sprawdza rozmiar pliku
    """
    if uploaded_file is None:
        return False, "Nie wybrano pliku"
    
    # Sprawdź rozmiar pliku (w bajtach)
    file_size = uploaded_file.size
    max_size_bytes = max_size_mb * 1024 * 1024
    
    if file_size > max_size_bytes:
        return False, f"Plik jest za duży. Maksymalny rozmiar: {max_size_mb}MB"
    
    return True, None

def get_supported_formats():
    """
    Zwraca listę obsługiwanych formatów plików
    """
    return {
        'txt': 'Pliki tekstowe (.txt)',
        'docx': 'Dokumenty Word (.docx)',
        'pdf': 'Dokumenty PDF (.pdf)'
    }

def create_file_upload_widget():
    """
    Tworzy widget do uploadowania plików
    """
    supported_formats = get_supported_formats()
    
    st.markdown("### 📁 **Wczytaj tekst z pliku**")
    
    # Informacje o obsługiwanych formatach
    st.info("**Obsługiwane formaty:**")
    for ext, desc in supported_formats.items():
        st.write(f"• {desc}")
    
    st.info("**Maksymalny rozmiar pliku:** 10MB")
    
    # Widget uploadowania
    uploaded_file = st.file_uploader(
        "Wybierz plik:",
        type=['txt', 'docx', 'pdf'],
        help="Kliknij 'Browse files' aby wybrać plik z tekstem"
    )
    
    if uploaded_file is not None:
        # Sprawdź rozmiar pliku
        size_valid, size_error = validate_file_size(uploaded_file)
        if not size_valid:
            st.error(size_error)
            return None, None
        
        # Wyciągnij tekst z pliku
        text, error = extract_text_from_file(uploaded_file)
        
        if error:
            st.error(f"❌ {error}")
            return None, None
        
        if text:
            # Pokaż podgląd tekstu
            st.success(f"✅ Pomyślnie wczytano plik: **{uploaded_file.name}**")
            st.info(f"**Rozmiar tekstu:** {len(text)} znaków")
            
            # Pokaż pierwsze 200 znaków jako podgląd
            preview = text[:200] + "..." if len(text) > 200 else text
            with st.expander("👁️ Podgląd tekstu (pierwsze 200 znaków)"):
                st.text(preview)
            
            return text, uploaded_file.name
        
    return None, None
