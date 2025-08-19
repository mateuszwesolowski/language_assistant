import streamlit as st
import os
from dotenv import load_dotenv
import openai
from datetime import datetime
import base64
from text_corrector import correct_text, get_correction_explanation
from grammar_helper import analyze_text, get_word_explanation
from audio_generator import generate_audio, get_available_voices, get_voice_for_language, save_audio_file
from database import LanguageHelperDB
from file_handler import create_file_upload_widget

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja OpenAI - tylko jeśli klucz API jest dostępny
client = None
if os.getenv("OPENAI_API_KEY"):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Konfiguracja strony
st.set_page_config(
    page_title="Pomocnik Językowy",
    page_icon="🌍",
    layout="wide"
)

# Tytuł aplikacji
st.title("🌍 Pomocnik Językowy")
st.markdown("---")

# Inicjalizacja bazy danych
db = LanguageHelperDB()

# Inicjalizacja sesji
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []
if 'correction_history' not in st.session_state:
    st.session_state.correction_history = []
if 'db_loaded' not in st.session_state:
    st.session_state.db_loaded = False
if 'current_session_action' not in st.session_state:
    st.session_state.current_session_action = None

def load_data_from_db():
    """Ładuje dane z bazy danych do sesji"""
    if not st.session_state.db_loaded:
        try:
            # Pobierz tłumaczenia z bazy danych
            translations = db.get_translations(limit=20)
            st.session_state.translation_history = translations
            
            # Pobierz poprawki i analizy z bazy danych
            corrections = db.get_corrections(limit=20)
            st.session_state.correction_history = corrections
            
            st.session_state.db_loaded = True
            print(f"✅ Załadowano {len(translations)} tłumaczeń i {len(corrections)} poprawek/analiz z bazy danych")
        except Exception as e:
            print(f"❌ Błąd podczas ładowania danych z bazy: {str(e)}")

def reload_data_from_db():
    """Ponownie ładuje dane z bazy danych do sesji"""
    try:
        # Pobierz tłumaczenia z bazy danych
        translations = db.get_translations(limit=20)
        st.session_state.translation_history = translations
        
        # Pobierz poprawki i analizy z bazy danych
        corrections = db.get_corrections(limit=20)
        st.session_state.correction_history = corrections
        
        print(f"✅ Ponownie załadowano {len(translations)} tłumaczeń i {len(corrections)} poprawek/analiz z bazy danych")
    except Exception as e:
        print(f"❌ Błąd podczas ponownego ładowania danych z bazy: {str(e)}")

def translate_text(text, target_language="angielski"):
    """
    Funkcja do tłumaczenia tekstu z polskiego na wybrany język
    """
    if not client:
        st.error("Klucz API OpenAI nie jest skonfigurowany. Dodaj OPENAI_API_KEY do pliku .env")
        return None
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": f"Jesteś ekspertem w tłumaczeniu tekstów. Tłumacz tekst z języka polskiego na {target_language}. Zwróć tylko przetłumaczony tekst, bez dodatkowych komentarzy."
                },
                {
                    "role": "user",
                    "content": f"Przetłumacz na {target_language}: {text}"
                }
            ],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Błąd podczas tłumaczenia: {str(e)}")
        return None

def main():
    # Ładuj dane z bazy danych przy pierwszym uruchomieniu
    load_data_from_db()
    
    # Sidebar z opcjami
    st.sidebar.header("⚙️ Opcje")
    
    # Wybór trybu pracy - NA GÓRZE MENU
    st.sidebar.markdown("### 🎯 **WYBIERZ TRYB PRACY**")
    mode = st.sidebar.selectbox(
        "Wybierz tryb pracy:",
        ["Tłumaczenie (PL → EN)", "Tłumaczenie (PL → Wybrany język)", "Poprawianie tekstu", "Analiza językowa"],
        index=0,
        key="mode_selector"
    )
    
    # Lista języków z flagami
    languages_with_flags = [
        "🇺🇸 angielski",
        "🇩🇪 niemiecki", 
        "🇫🇷 francuski",
        "🇪🇸 hiszpański",
        "🇮🇹 włoski",
        "🇷🇺 rosyjski",
        "🇯🇵 japoński",
        "🇰🇷 koreański",
        "🇨🇳 chiński"
    ]
    
    # Słownik do mapowania nazw z flagami na nazwy bez flag
    language_mapping = {
        "🇺🇸 angielski": "angielski",
        "🇩🇪 niemiecki": "niemiecki",
        "🇫🇷 francuski": "francuski", 
        "🇪🇸 hiszpański": "hiszpański",
        "🇮🇹 włoski": "włoski",
        "🇷🇺 rosyjski": "rosyjski",
        "🇯🇵 japoński": "japoński",
        "🇰🇷 koreański": "koreański",
        "🇨🇳 chiński": "chiński"
    }
    
    # Wybór języka docelowego - BEZPOŚREDNIO POD TRYBEM
    if "Wybrany język" in mode:
        st.sidebar.markdown("### 🌍 **WYBIERZ JĘZYK DOCELOWY**")
        selected_language_with_flag = st.sidebar.selectbox(
            "Język docelowy:",
            languages_with_flags,
            index=0
        )
        target_language = language_mapping[selected_language_with_flag]
    elif "Poprawianie" in mode:
        st.sidebar.markdown("### 🔧 **WYBIERZ JĘZYK TEKSTU**")
        selected_language_with_flag = st.sidebar.selectbox(
            "Język tekstu do poprawienia:",
            languages_with_flags,
            index=0
        )
        target_language = language_mapping[selected_language_with_flag]
    elif "Analiza" in mode:
        st.sidebar.markdown("### 📊 **WYBIERZ JĘZYK ANALIZY**")
        selected_language_with_flag = st.sidebar.selectbox(
            "Język analizy:",
            languages_with_flags,
            index=0
        )
        target_language = language_mapping[selected_language_with_flag]
    else:
        target_language = "angielski"
    
    st.sidebar.markdown("---")
    
    # Przyciski do zarządzania historią
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🔄 Odśwież", key="refresh_history", help="Odśwież historię z bazy danych"):
            reload_data_from_db()
            st.success("✅ Historia została odświeżona z bazy danych!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Wyczyść", key="clear_history", help="Wyczyść całą historię"):
            st.session_state.translation_history = []
            st.session_state.correction_history = []
            # Wyczyść również bazę danych
            if db.clear_all():
                st.success("✅ Historia została wyczyszczona z pamięci i bazy danych!")
            else:
                st.warning("⚠️ Historia została wyczyszczona z pamięci, ale wystąpił błąd z bazy danych")
            st.rerun()
    
    # Statystyki bazy danych
    stats = db.get_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Statystyki bazy danych:**")
    st.sidebar.info(f"Status: {stats['status']}")
    st.sidebar.info(f"Liczba rekordów: {stats['total_points']}")
    
    # Wyczyść historię gdy zmienia się tryb
    if 'previous_mode' not in st.session_state:
        st.session_state.previous_mode = mode
    
    if st.session_state.previous_mode != mode:
        # Aktualizuj poprzedni tryb
        st.session_state.previous_mode = mode
        # Wyczyść aktualny wynik sesji przy zmianie trybu
        st.session_state.current_session_action = None
        # Załaduj dane z bazy danych po zmianie trybu
        reload_data_from_db()
        st.rerun()
    
    # Główny obszar aplikacji
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Wprowadź tekst")
        
        # Opcje wprowadzania tekstu
        input_method = st.radio(
            "Wybierz sposób wprowadzania tekstu:",
            ["✏️ Wpisz tekst ręcznie", "📁 Wczytaj z pliku"],
            horizontal=True,
            key="input_method"
        )
        
        if input_method == "📁 Wczytaj z pliku":
            # Widget do uploadowania plików
            file_text, file_name = create_file_upload_widget()
            
            if file_text:
                # Pokaż wczytany tekst w polu tekstowym
                st.markdown("**📄 Wczytany tekst:**")
                input_text = st.text_area(
                    "Tekst z pliku:",
                    value=file_text,
                    height=200,
                    key="file_text_area"
                )
            else:
                input_text = ""
        else:
            # Pole tekstowe
            if "Tłumaczenie" in mode:
                placeholder = "Wpisz tutaj tekst w języku polskim do przetłumaczenia..."
                label = "Wpisz tekst w języku polskim:"
            elif "Poprawianie" in mode:
                placeholder = f"Wpisz tutaj tekst w języku {target_language} do poprawienia (błędy będą wyjaśnione po polsku)..."
                label = f"Wpisz tekst w języku {target_language}:"
            else:  # Analiza językowa
                placeholder = f"Wpisz tutaj tekst w języku {target_language} do analizy (wyjaśnienia będą po polsku)..."
                label = f"Wpisz tekst w języku {target_language}:"
            
            input_text = st.text_area(
                label,
                height=200,
                placeholder=placeholder
            )
        
        # Przycisk akcji
        if "Tłumaczenie" in mode:
            button_text = "🔄 Przetłumacz"
            button_type = "primary"
        elif "Poprawianie" in mode:
            button_text = "🔧 Popraw tekst"
            button_type = "primary"
        else:  # Analiza językowa
            button_text = "📊 Analizuj tekst"
            button_type = "primary"
        
        if st.button(button_text, type=button_type, use_container_width=True, key=f"main_action_{mode.replace(' ', '_').replace('(', '').replace(')', '').replace('→', '_to_')}"):
            if input_text.strip():
                with st.spinner("Przetwarzam..."):
                    if "Tłumaczenie" in mode:
                        result = translate_text(input_text, target_language)
                        if result:
                            # Generuj audio dla tłumaczenia
                            voice = get_voice_for_language(target_language)
                            audio_data = generate_audio(result, voice)
                            
                            # Zapisz do bazy danych
                            db_id = db.save_translation(
                                input_text=input_text,
                                output_text=result,
                                target_language=target_language,
                                mode='translation',
                                audio_data=audio_data,
                                voice=voice
                            )
                            
                            # Dodaj do sesji
                            translation_item = {
                                'id': db_id,
                                'timestamp': datetime.now(),
                                'input': input_text,
                                'output': result,
                                'target_language': target_language,
                                'mode': 'translation',
                                'audio_data': audio_data,
                                'voice': voice
                            }
                            st.session_state.translation_history.append(translation_item)
                            # Ustaw aktualny wynik sesji
                            st.session_state.current_session_action = translation_item
                            st.success("✅ Tłumaczenie zakończone i zapisane w bazie danych!")
                    elif "Poprawianie" in mode:
                        corrected = correct_text(input_text, target_language)
                        if corrected:
                            explanation = get_correction_explanation(input_text, corrected, target_language)
                            # Zapisz do bazy danych
                            db_id = db.save_correction(
                                input_text=input_text,
                                output_text=corrected,
                                explanation=explanation,
                                language=target_language,
                                mode='correction'
                            )
                            
                            # Dodaj do sesji
                            correction_item = {
                                'id': db_id,
                                'timestamp': datetime.now(),
                                'input': input_text,
                                'output': corrected,
                                'explanation': explanation,
                                'language': target_language,
                                'mode': 'correction'
                            }
                            st.session_state.correction_history.append(correction_item)
                            # Ustaw aktualny wynik sesji
                            st.session_state.current_session_action = correction_item
                            st.success("✅ Poprawianie zakończone i zapisane w bazie danych!")
                    else:  # Analiza językowa
                        analysis = analyze_text(input_text, target_language)
                        # Zapisz do bazy danych
                        db_id = db.save_correction(
                            input_text=input_text,
                            output_text="",  # Analiza nie ma output_text
                            explanation=str(analysis),  # Zapisujemy analizę jako explanation
                            language=target_language,
                            mode='analysis'
                        )
                        
                        # Dodaj do sesji
                        analysis_item = {
                            'id': db_id,
                            'timestamp': datetime.now(),
                            'input': input_text,
                            'analysis': analysis,
                            'language': target_language,
                            'mode': 'analysis'
                        }
                        st.session_state.correction_history.append(analysis_item)
                        # Ustaw aktualny wynik sesji
                        st.session_state.current_session_action = analysis_item
                        st.success("✅ Analiza zakończona i zapisana w bazie danych!")
            else:
                st.warning("⚠️ Wprowadź tekst do przetworzenia.")
    
    with col2:
        st.subheader("🎯 Wynik")
        
        # Pokaż aktualny tryb
        mode_icons = {
            "Tłumaczenie (PL → EN)": "🔄",
            "Tłumaczenie (PL → Wybrany język)": "🌍",
            "Poprawianie tekstu": "🔧",
            "Analiza językowa": "📊"
        }
        
        current_icon = mode_icons.get(mode, "⚙️")
        st.info(f"{current_icon} **Tryb:** {mode}")
        
        # Wyświetl ostatni wynik tylko jeśli był wykonany w tej sesji
        if st.session_state.current_session_action:
            latest = st.session_state.current_session_action
            
            if latest['mode'] == 'translation':
                st.markdown(f"**Oryginalny tekst:**")
                st.info(latest['input'])
                st.markdown(f"**Przetłumaczony tekst ({latest['target_language']}):**")
                st.success(latest['output'])
                
                # Przycisk do kopiowania
                if st.button("📋 Kopiuj tłumaczenie", use_container_width=True, key="copy_latest"):
                    st.write("Skopiowano do schowka!")
                    
                # Wyświetl audio jeśli jest dostępne w historii
                if 'audio_data' in latest and latest['audio_data']:
                    st.markdown("**🔊 Audio:**")
                    st.info(f"Głos: {latest.get('voice', 'alloy')}")
                    
                    # Sprawdź czy dane audio są poprawne
                    if len(latest['audio_data']) < 1000:
                        st.error("❌ Dane audio są uszkodzone lub za małe")
                    else:
                        # Zapisz audio do pliku tymczasowego dla lepszej kompatybilności
                        import tempfile
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                            temp_file.write(latest['audio_data'])
                            temp_file_path = temp_file.name
                        
                        # Sprawdź czy plik został utworzony
                        if os.path.exists(temp_file_path) and os.path.getsize(temp_file_path) > 0:
                            try:
                                # Wyświetl audio z pliku
                                st.audio(temp_file_path, format="audio/wav")
                            except Exception as e:
                                st.error(f"❌ Błąd odtwarzania audio: {str(e)}")
                                # Alternatywnie: wyświetl jako base64
                                st.info("💡 Spróbuj pobrać plik audio i odtworzyć lokalnie")
                        else:
                            st.error("❌ Nie udało się utworzyć pliku audio")
                    
                    # Przycisk pobierania
                    st.download_button(
                        label="📥 Pobierz audio",
                        data=latest['audio_data'],
                        file_name=f"translation_{latest['timestamp'].strftime('%Y%m%d_%H%M%S')}.wav",
                        mime="audio/wav",
                        key=f"download_latest_{latest['timestamp'].strftime('%Y%m%d_%H%M%S')}"
                    )
                else:
                    # Jeśli audio nie jest dostępne, pokaż przycisk do generowania
                    if st.button("🔊 Generuj audio", use_container_width=True, key="generate_audio_latest"):
                        with st.spinner("Generuję audio..."):
                            try:
                                voice = get_voice_for_language(latest['target_language'])
                                st.info(f"Używam głosu: {voice}")
                                
                                audio_data = generate_audio(latest['output'], voice)
                                if audio_data:
                                    # Zaktualizuj historię z audio
                                    latest['audio_data'] = audio_data
                                    latest['voice'] = voice
                                    
                                    st.success(f"✅ Audio wygenerowane! Rozmiar: {len(audio_data)} bajtów")
                                    st.rerun()  # Odśwież stronę aby pokazać audio
                                else:
                                    st.error("❌ Nie udało się wygenerować audio. Sprawdź klucz API OpenAI.")
                            except Exception as e:
                                st.error(f"❌ Błąd podczas generowania audio: {str(e)}")
                                st.info("💡 Sprawdź czy masz wystarczające środki na koncie OpenAI")
                            
            elif latest['mode'] == 'correction':
                st.markdown(f"**Oryginalny tekst:**")
                st.info(latest['input'])
                st.markdown(f"**Poprawiony tekst:**")
                st.success(latest['output'])
                
                st.markdown("**Wyjaśnienie poprawek:**")
                st.write(latest['explanation'])
                
                # Przycisk do kopiowania poprawionego tekstu
                if st.button("📋 Kopiuj poprawiony tekst", use_container_width=True, key="copy_correction"):
                    st.write("Skopiowano do schowka!")
                            
            elif latest['mode'] == 'analysis':
                st.markdown(f"**Analizowany tekst:**")
                st.info(latest['input'])
                
                # Wyświetl analizę
                analysis = latest['analysis']
                
                # Słownictwo
                if analysis.vocabulary_items:
                    st.markdown("**📚 Słownictwo:**")
                    for item in analysis.vocabulary_items[:3]:  # Pokaż pierwsze 3
                        with st.expander(f"{item.word} - {item.translation}"):
                            st.write(f"**Część mowy:** {item.part_of_speech}")
                            st.write(f"**Przykład:** {item.example_sentence}")
                            st.write(f"**Poziom:** {item.difficulty_level}")
                
                # Reguły gramatyczne
                if analysis.grammar_rules:
                    st.markdown("**📖 Reguły gramatyczne:**")
                    for rule in analysis.grammar_rules[:2]:  # Pokaż pierwsze 2
                        with st.expander(f"{rule.rule_name}"):
                            st.write(f"**Wyjaśnienie:** {rule.explanation}")
                            st.write("**Przykłady:**")
                            for example in rule.examples[:2]:
                                st.write(f"- {example}")
                            st.write(f"**Poziom:** {rule.difficulty_level}")
                
                # Wskazówki do nauki
                if analysis.learning_tips:
                    st.markdown("**💡 Wskazówki do nauki:**")
                    for tip in analysis.learning_tips[:3]:
                        st.write(f"• {tip}")
        else:
            # Pokaż odpowiedni komunikat dla każdego trybu
            if "Tłumaczenie" in mode:
                st.info("👈 Wprowadź tekst w języku polskim i kliknij 'Przetłumacz' aby zobaczyć wynik.")
            elif "Poprawianie" in mode:
                st.info(f"👈 Wprowadź tekst w języku {target_language} i kliknij 'Popraw tekst' aby zobaczyć poprawki z wyjaśnieniami po polsku.")
            elif "Analiza" in mode:
                st.info(f"👈 Wprowadź tekst w języku {target_language} i kliknij 'Analizuj tekst' aby zobaczyć analizę z wyjaśnieniami po polsku.")
            else:
                st.info("👈 Wprowadź tekst i kliknij przycisk aby zobaczyć wynik.")
    
    # Historia - pokazuj tylko historię odpowiednią dla danego trybu
    if "Tłumaczenie" in mode:
        # Historia tłumaczeń
        if st.session_state.translation_history:
            st.markdown("---")
            st.subheader("📚 Historia tłumaczeń")
            
            # Wyświetl ostatnie 5 tłumaczeń
            for i, item in enumerate(reversed(st.session_state.translation_history[-5:])):
                if item['mode'] == 'translation':
                    with st.expander(f"Tłumaczenie {len(st.session_state.translation_history) - i} - {item['timestamp'].strftime('%H:%M:%S')}"):
                        # Przycisk usuwania
                        col_delete, col_content = st.columns([1, 10])
                        with col_delete:
                            if st.button("🗑️", key=f"delete_translation_{item.get('id', i)}", help="Usuń z bazy danych"):
                                if 'id' in item and db.delete_item(item['id']):
                                    st.session_state.translation_history.remove(item)
                                    st.success("✅ Usunięto z bazy danych!")
                                    st.rerun()
                                else:
                                    st.error("❌ Błąd podczas usuwania")
                        with col_content:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Oryginalny:**")
                                st.write(item['input'])
                            with col_b:
                                st.markdown(f"**Przetłumaczony ({item['target_language']}):**")
                                st.write(item['output'])
                        
                        # Wyświetl audio jeśli jest dostępne
                        if 'audio_data' in item and item['audio_data']:
                            st.markdown("**🔊 Audio:**")
                            st.info(f"Głos: {item.get('voice', 'alloy')}")
                            
                            # Zapisz audio do pliku tymczasowego
                            import tempfile
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                                temp_file.write(item['audio_data'])
                                temp_file_path = temp_file.name
                            
                            # Wyświetl audio
                            st.audio(temp_file_path, format="audio/wav")
                            
                            # Przycisk pobierania
                            st.download_button(
                                label="📥 Pobierz audio",
                                data=item['audio_data'],
                                file_name=f"translation_{item['timestamp'].strftime('%Y%m%d_%H%M%S')}.wav",
                                mime="audio/wav",
                                key=f"download_history_{item['timestamp'].strftime('%Y%m%d_%H%M%S')}_{i}"
                            )
                        else:
                            st.info("🔇 Audio nie jest dostępne dla tego tłumaczenia")
    
    elif "Poprawianie" in mode:
        # Historia poprawek
        if st.session_state.correction_history:
            st.markdown("---")
            st.subheader("🔧 Historia poprawek")
            
            for i, item in enumerate(reversed(st.session_state.correction_history[-3:])):
                if item['mode'] == 'correction':
                    with st.expander(f"Poprawka {len(st.session_state.correction_history) - i} - {item['timestamp'].strftime('%H:%M:%S')}"):
                        # Przycisk usuwania
                        col_delete, col_content = st.columns([1, 10])
                        with col_delete:
                            if st.button("🗑️", key=f"delete_correction_{item.get('id', i)}", help="Usuń z bazy danych"):
                                if 'id' in item and db.delete_item(item['id']):
                                    st.session_state.correction_history.remove(item)
                                    st.success("✅ Usunięto z bazy danych!")
                                    st.rerun()
                                else:
                                    st.error("❌ Błąd podczas usuwania")
                        with col_content:
                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**Oryginalny:**")
                                st.write(item['input'])
                            with col_b:
                                st.markdown("**Poprawiony:**")
                                st.write(item['output'])
                            
                            st.markdown("**Wyjaśnienie poprawek:**")
                            st.write(item['explanation'])
    
    elif "Analiza" in mode:
        # Historia analiz
        if st.session_state.correction_history:
            st.markdown("---")
            st.subheader("📊 Historia analiz")
            
            for i, item in enumerate(reversed(st.session_state.correction_history[-3:])):
                if item['mode'] == 'analysis':
                    with st.expander(f"Analiza {len(st.session_state.correction_history) - i} - {item['timestamp'].strftime('%H:%M:%S')}"):
                        # Przycisk usuwania
                        col_delete, col_content = st.columns([1, 10])
                        with col_delete:
                            if st.button("🗑️", key=f"delete_analysis_{item.get('id', i)}", help="Usuń z bazy danych"):
                                if 'id' in item and db.delete_item(item['id']):
                                    st.session_state.correction_history.remove(item)
                                    st.success("✅ Usunięto z bazy danych!")
                                    st.rerun()
                                else:
                                    st.error("❌ Błąd podczas usuwania")
                        with col_content:
                            st.markdown("**Analizowany tekst:**")
                            st.write(item['input'])
                            st.markdown(f"**Język:** {item['language']}")
                            
                            # Wyświetl analizę jeśli jest dostępna
                            if 'analysis' in item and item['analysis']:
                                analysis = item['analysis']
                                
                                # Słownictwo
                                if analysis.vocabulary_items:
                                    st.markdown("**📚 Słownictwo:**")
                                    for vocab_item in analysis.vocabulary_items[:2]:
                                        st.write(f"• **{vocab_item.word}** - {vocab_item.translation} ({vocab_item.part_of_speech})")
                                
                                # Reguły gramatyczne
                                if analysis.grammar_rules:
                                    st.markdown("**📖 Reguły gramatyczne:**")
                                    for rule in analysis.grammar_rules[:1]:
                                        st.write(f"• **{rule.rule_name}** - {rule.explanation}")
                                
                                # Wskazówki do nauki
                                if analysis.learning_tips:
                                    st.markdown("**💡 Wskazówki:**")
                                    for tip in analysis.learning_tips[:2]:
                                        st.write(f"• {tip}")

if __name__ == "__main__":
    main()
