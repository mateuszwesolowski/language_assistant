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
from tutor_agent import TutorAgent

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja OpenAI - tylko jeśli klucz API jest dostępny
client = None
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = openai.OpenAI(api_key=api_key)
else:
    print("❌ Błąd: Brak klucza API OpenAI w zmiennych środowiskowych")

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

# Inicjalizacja agenta korepetytora
tutor_agent = None
if client:
    tutor_agent = TutorAgent(client, db)
else:
    print("❌ Błąd: Nie można utworzyć tutor agent - brak klienta OpenAI")

# Inicjalizacja sesji
if 'translation_history' not in st.session_state:
    st.session_state.translation_history = []
if 'correction_history' not in st.session_state:
    st.session_state.correction_history = []
if 'db_loaded' not in st.session_state:
    st.session_state.db_loaded = False
if 'current_session_action' not in st.session_state:
    st.session_state.current_session_action = None
if 'chat_sessions_history' not in st.session_state:
    st.session_state.chat_sessions_history = []
if 'tips_history' not in st.session_state:
    st.session_state.tips_history = []

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
            
            # Pobierz sesje czatu z bazy danych
            chat_sessions = db.get_chat_sessions(limit=20)
            st.session_state.chat_sessions_history = chat_sessions
            
            # Pobierz historię wskazówek z bazy danych
            tips_history = db.get_learning_tips_history(limit=20)
            st.session_state.tips_history = tips_history
            
            st.session_state.db_loaded = True
            print(f"✅ Załadowano {len(translations)} tłumaczeń, {len(corrections)} poprawek/analiz, {len(chat_sessions)} sesji czatu i {len(tips_history)} wskazówek z bazy danych")
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
        
        # Pobierz sesje czatu z bazy danych
        chat_sessions = db.get_chat_sessions(limit=20)
        st.session_state.chat_sessions_history = chat_sessions
        
        # Pobierz historię wskazówek z bazy danych
        tips_history = db.get_learning_tips_history(limit=20)
        st.session_state.tips_history = tips_history
        
        print(f"✅ Ponownie załadowano {len(translations)} tłumaczeń, {len(corrections)} poprawek/analiz, {len(chat_sessions)} sesji czatu i {len(tips_history)} wskazówek z bazy danych")
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
    
    # Określ indeks na podstawie mode_selector
    mode_options = ["Tłumaczenie (PL → EN)", "Tłumaczenie (PL → Wybrany język)", "Poprawianie tekstu", "Analiza językowa", "🔄 Powtarzacz"]
    current_mode = st.session_state.get('mode_selector', "Tłumaczenie (PL → EN)")
    current_index = mode_options.index(current_mode) if current_mode in mode_options else 0
    
    mode = st.sidebar.selectbox(
        "Wybierz tryb pracy:",
        mode_options,
        index=current_index,
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
    elif "Powtarzacz" in mode:
        st.sidebar.markdown("### 🔄 **WYBIERZ JĘZYK POWTARZANIA**")
        selected_language_with_flag = st.sidebar.selectbox(
            "Język powtarzania:",
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
    
    with col2:
        if st.button("🗑️ Wyczyść", key="clear_history", help="Wyczyść całą historię"):
            st.session_state.translation_history = []
            st.session_state.correction_history = []
            # Wyczyść również bazę danych
            if db.clear_all():
                st.success("✅ Historia została wyczyszczona z pamięci i bazy danych!")
            else:
                st.warning("⚠️ Historia została wyczyszczona z pamięci, ale wystąpił błąd z bazy danych")
    
    # Statystyki bazy danych
    stats = db.get_stats()
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Statystyki bazy danych:**")
    st.sidebar.info(f"Status: {stats['status']}")
    st.sidebar.info(f"Liczba rekordów: {stats['total_points']}")
    

    

    
    # Wyczyść aktualny wynik przy zmianie trybu
    if 'previous_mode' not in st.session_state:
        st.session_state.previous_mode = mode
    elif st.session_state.previous_mode != mode:
        st.session_state.current_session_action = None
        st.session_state.previous_mode = mode
    
    # Dynamiczny opis sekcji pod nagłówkiem
    if "Tłumaczenie" in mode:
        st.info("📚 **Tłumaczenie tekstu** - Przetłumacz tekst między różnymi językami z pomocą AI. Wybierz język źródłowy i docelowy, wprowadź tekst i otrzymaj profesjonalne tłumaczenie.")
    elif "Poprawianie" in mode:
        st.info("✏️ **Poprawianie tekstu** - Popraw błędy gramatyczne, ortograficzne i stylistyczne w tekście. AI przeanalizuje Twój tekst i zaproponuje poprawki z wyjaśnieniami.")
    elif "Analiza językowa" in mode:
        st.info("🔍 **Analiza językowa** - Głęboka analiza tekstu obejmująca strukturę gramatyczną, styl, trudność i sugestie poprawy. Idealne do nauki i doskonalenia umiejętności językowych.")
    elif "Powtarzacz" in mode:
        st.info("🔄 **Powtarzacz - Inteligentny korepetytor językowy** - Osobisty asystent do nauki języka z generowaniem wskazówek, ćwiczeń i interaktywnym chatem. Wykorzystuje Twoją historię nauki do personalizacji.")
    
    st.markdown("---")
    
    # Główny obszar aplikacji
    if "Powtarzacz" in mode:
        # Sekcja Powtarzacz z 3 podsekcjami
        st.subheader("🔄 Powtarzacz - Twój Osobisty Korepetytor")
        st.info(f"🎓 Wybierz sekcję i pracuj z korepetytorem języka {target_language}!")
        
        # Sprawdź czy należy przejść do chatu
        if 'go_to_chat' in st.session_state and st.session_state.go_to_chat:
            default_index = 2  # Chat z korepetytorem
            st.session_state.go_to_chat = False  # Reset flagi
        elif 'current_subsection' in st.session_state:
            # Zachowaj aktualną sekcję
            subsection_options = ["💡 Wskazówki do nauki", "🎯 Ćwiczenia", "💬 Chat z korepetytorem"]
            try:
                default_index = subsection_options.index(st.session_state.current_subsection)
            except ValueError:
                default_index = 0
        else:
            default_index = 0  # Domyślnie wskazówki
        
        # Wybór podsekcji
        subsection = st.radio(
            "Wybierz sekcję:",
            ["💡 Wskazówki do nauki", "🎯 Ćwiczenia", "💬 Chat z korepetytorem"],
            horizontal=True,
            index=default_index,
            key="subsection_selector"
        )
        
        # Zapisz aktualną sekcję
        st.session_state.current_subsection = subsection
        
        st.markdown("---")
        
        # 1. SEKCJA WSKAZÓWEK DO NAUKI
        if subsection == "💡 Wskazówki do nauki":
            st.subheader("💡 Generowanie wskazówek do nauki")
            st.info("Korepetytor przeanalizuje Twoją historię nauki i wygeneruje spersonalizowane wskazówki!")
            
            if tutor_agent:
                col_generate, col_archive = st.columns([2, 1])
                
                with col_generate:
                    if st.button("💡 Generuj wskazówki do nauki", use_container_width=True, key="generate_tips_main"):
                        with st.spinner("Analizuję Twoją historię i generuję wskazówki..."):
                            tips = tutor_agent.get_learning_tips(target_language)
                            if tips and "error" not in tips[0].lower():
                                st.session_state.learning_tips = tips
                                # Zapisz wskazówki do bazy danych
                                db.save_learning_tips(tips, target_language)
                                # Odśwież dane z bazy danych
                                reload_data_from_db()
                                st.success("✅ Wskazówki wygenerowane i zapisane w archiwum!")
                            else:
                                st.error(f"❌ Błąd podczas generowania wskazówek: {tips[0] if tips else 'Nieznany błąd'}")
                
                with col_archive:
                    if st.button("📚 Pokaż archiwum wskazówek", use_container_width=True, key="show_tips_archive"):
                        st.session_state.open_tips_archive = True
                        st.rerun()
                
                # Wyświetl wskazówki jeśli są dostępne
                if 'learning_tips' in st.session_state and st.session_state.learning_tips:
                    st.markdown("---")
                    st.subheader("💡 Twoje spersonalizowane wskazówki:")
                    for i, tip in enumerate(st.session_state.learning_tips, 1):
                        st.info(f"**{i}.** {tip}")
                    
                    # Przycisk do zapisania wskazówek w chacie
                    if st.button("💬 Przejdź do chatu z tymi wskazówkami", use_container_width=True, key="go_to_chat_with_tips"):
                        st.session_state.chat_context = f"Wskazówki do nauki: {' '.join(st.session_state.learning_tips)}"
                        st.session_state.go_to_chat = True
                        st.rerun()
                
                # Wyświetl archiwum wskazówek
                if 'open_tips_archive' in st.session_state and st.session_state.open_tips_archive:
                    st.markdown("---")
                    st.subheader("📚 Archiwum wskazówek do nauki")
                    
                    if st.session_state.tips_history:
                        for i, tip_item in enumerate(st.session_state.tips_history[:5]):  # Pokaż ostatnie 5
                            with st.expander(f"Wskazówki z {tip_item['timestamp'].strftime('%d.%m.%Y %H:%M')} - {tip_item['language']}"):
                                tips_list = tip_item['tips_text'].split('\n')
                                for tip in tips_list:
                                    if tip.strip():
                                        st.info(tip.strip())
                                
                                col_load, col_delete = st.columns([3, 1])
                                with col_load:
                                    if st.button(f"💬 Przejdź do chatu z tymi wskazówkami", key=f"load_tips_chat_{i}"):
                                        st.session_state.chat_context = f"Wskazówki do nauki: {tip_item['tips_text']}"
                                        st.session_state.go_to_chat = True
                                        st.rerun()
                                with col_delete:
                                    if st.button(f"🗑️ Usuń", key=f"delete_tips_{i}"):
                                        if db.delete_item(tip_item['id']):
                                            st.success("✅ Wskazówki usunięte z archiwum!")
                                            st.rerun()
                    else:
                        st.info("📭 Brak zapisanych wskazówek w archiwum")
                    
                    if st.button("❌ Zamknij archiwum", key="close_tips_archive"):
                        st.session_state.open_tips_archive = False
                        st.rerun()
            else:
                st.error("❌ Agent korepetytor nie jest dostępny. Sprawdź klucz API OpenAI.")
        
        # 2. SEKCJA ĆWICZEŃ
        elif subsection == "🎯 Ćwiczenia":
            st.subheader("🎯 Generowanie ćwiczeń")
            st.info("Korepetytor stworzy spersonalizowane ćwiczenia na podstawie Twojej historii nauki!")
            
            if tutor_agent:
                # Wybór typu ćwiczenia
                exercise_type = st.selectbox(
                    "Wybierz typ ćwiczenia:",
                    ["vocabulary", "grammar", "translation"],
                    format_func=lambda x: {
                        "vocabulary": "📚 Słownictwo",
                        "grammar": "📖 Gramatyka", 
                        "translation": "🔄 Tłumaczenie"
                    }[x],
                    key="exercise_type_selector"
                )
                
                col_generate_ex, col_archive_ex = st.columns([2, 1])
                
                with col_generate_ex:
                    if st.button("🎯 Generuj ćwiczenie", use_container_width=True, key="generate_exercise_main"):
                        with st.spinner(f"Generuję ćwiczenie z {exercise_type}..."):
                            exercise = tutor_agent.generate_exercise(target_language, exercise_type)
                            if "error" not in exercise:
                                # Zapisz do bazy danych
                                db_id = db.save_correction(
                                    input_text="",
                                    output_text="",
                                    explanation="",
                                    language=target_language,
                                    mode='exercise',
                                    analysis_data=exercise
                                )
                                
                                # Zapisz ćwiczenie do sesji
                                exercise_item = {
                                    'id': db_id,
                                    'timestamp': datetime.now(),
                                    'exercise': exercise,
                                    'language': target_language,
                                    'mode': 'exercise'
                                }
                                st.session_state.correction_history.append(exercise_item)
                                st.session_state.current_exercise = exercise_item
                                # Odśwież dane z bazy danych
                                reload_data_from_db()
                                st.success("✅ Ćwiczenie wygenerowane i zapisane w archiwum!")
                            else:
                                st.error(f"❌ Błąd: {exercise['error']}")
                
                with col_archive_ex:
                    if st.button("📚 Pokaż archiwum ćwiczeń", use_container_width=True, key="show_exercise_archive"):
                        st.session_state.open_exercise_archive = True
                        st.rerun()
                
                # Wyświetl ostatnie ćwiczenie
                if 'current_exercise' in st.session_state and st.session_state.current_exercise:
                    st.markdown("---")
                    st.subheader("🎯 Ostatnie ćwiczenie")
                    latest = st.session_state.current_exercise
                    exercise = latest['exercise']
                    
                    st.markdown(f"**🎯 {exercise.get('title', 'Ćwiczenie')}**")
                    st.info(exercise.get('description', ''))
                    
                    st.markdown("**❓ Pytanie:**")
                    st.write(exercise.get('question', ''))
                    
                    # Wyświetl opcje dla ćwiczeń ze słownictwa
                    if exercise.get('type') == 'vocabulary' and 'options' in exercise:
                        st.markdown("**📝 Opcje odpowiedzi:**")
                        for i, option in enumerate(exercise['options'], 1):
                            st.write(f"{i}. {option}")
                    
                    # Przyciski akcji
                    col_show_answer, col_new_exercise, col_chat = st.columns(3)
                    
                    with col_show_answer:
                        if st.button("🔍 Pokaż odpowiedź", use_container_width=True, key="show_answer_exercise"):
                            st.markdown("**✅ Poprawna odpowiedź:**")
                            st.success(exercise.get('correct_answer', ''))
                            
                            st.markdown("**📖 Wyjaśnienie:**")
                            st.write(exercise.get('explanation', ''))
                            
                            if 'hint' in exercise and exercise['hint']:
                                st.markdown("**💡 Podpowiedź:**")
                                st.info(exercise['hint'])
                    
                    with col_new_exercise:
                        if st.button("🔄 Nowe ćwiczenie", use_container_width=True, key="new_exercise"):
                            with st.spinner(f"Generuję nowe ćwiczenie z {exercise_type}..."):
                                new_exercise = tutor_agent.generate_exercise(target_language, exercise_type)
                                if "error" not in new_exercise:
                                    # Zapisz do bazy danych
                                    db_id = db.save_correction(
                                        input_text="",
                                        output_text="",
                                        explanation="",
                                        language=target_language,
                                        mode='exercise',
                                        analysis_data=new_exercise
                                    )
                                    
                                    # Zapisz nowe ćwiczenie do sesji
                                    new_exercise_item = {
                                        'id': db_id,
                                        'timestamp': datetime.now(),
                                        'exercise': new_exercise,
                                        'language': target_language,
                                        'mode': 'exercise'
                                    }
                                    st.session_state.correction_history.append(new_exercise_item)
                                    st.session_state.current_exercise = new_exercise_item
                                    # Odśwież dane z bazy danych
                                    reload_data_from_db()
                                    st.success("✅ Nowe ćwiczenie wygenerowane i zapisane!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Błąd podczas generowania nowego ćwiczenia: {new_exercise['error']}")
                    
                    with col_chat:
                        if st.button("💬 Przejdź do chatu z tym ćwiczeniem", use_container_width=True, key="go_to_chat_with_exercise"):
                            st.session_state.chat_context = f"Ostatnie ćwiczenie: {exercise.get('title', 'Ćwiczenie')} - {exercise.get('question', '')} - Odpowiedź: {exercise.get('correct_answer', '')}"
                            st.session_state.go_to_chat = True
                            st.rerun()
                
                # Wyświetl archiwum ćwiczeń
                if 'open_exercise_archive' in st.session_state and st.session_state.open_exercise_archive:
                    st.markdown("---")
                    st.subheader("📚 Archiwum ćwiczeń")
                    
                    # Filtruj ćwiczenia z historii
                    exercise_history = [item for item in st.session_state.correction_history if item.get('mode') == 'exercise']
                    
                    if exercise_history:
                        for i, exercise_item in enumerate(exercise_history[:5]):  # Pokaż ostatnie 5
                            exercise = exercise_item['exercise']
                            with st.expander(f"Ćwiczenie z {exercise_item['timestamp'].strftime('%d.%m.%Y %H:%M')} - {exercise.get('title', 'Ćwiczenie')}"):
                                st.markdown(f"**🎯 {exercise.get('title', 'Ćwiczenie')}**")
                                st.info(exercise.get('description', ''))
                                st.markdown(f"**❓ Pytanie:** {exercise.get('question', '')}")
                                
                                if exercise.get('type') == 'vocabulary' and 'options' in exercise:
                                    st.markdown("**📝 Opcje:**")
                                    for j, option in enumerate(exercise['options'], 1):
                                        st.write(f"{j}. {option}")
                                
                                col_load_ex, col_delete_ex = st.columns([3, 1])
                                with col_load_ex:
                                    if st.button(f"💬 Przejdź do chatu z tym ćwiczeniem", key=f"load_exercise_chat_{i}"):
                                        st.session_state.chat_context = f"Ćwiczenie: {exercise.get('title', 'Ćwiczenie')} - {exercise.get('question', '')} - Odpowiedź: {exercise.get('correct_answer', '')}"
                                        st.session_state.go_to_chat = True
                                        st.rerun()
                                with col_delete_ex:
                                    if st.button(f"🗑️ Usuń", key=f"delete_exercise_{i}"):
                                        if db.delete_item(exercise_item['id']):
                                            st.success("✅ Ćwiczenie usunięte z archiwum!")
                                            st.rerun()
                    else:
                        st.info("📭 Brak zapisanych ćwiczeń w archiwum")
                    
                    if st.button("❌ Zamknij archiwum", key="close_exercise_archive"):
                        st.session_state.open_exercise_archive = False
                        st.rerun()
        
                # Wyświetl archiwum sesji czatu
        if 'open_chat_archive' in st.session_state and st.session_state.open_chat_archive:
            st.markdown("---")
            st.subheader("📚 Archiwum sesji czatu")
            
            if st.session_state.chat_sessions_history:
                for i, chat_session in enumerate(st.session_state.chat_sessions_history[:5]):  # Pokaż ostatnie 5
                    with st.expander(f"Sesja z {chat_session['timestamp'].strftime('%d.%m.%Y %H:%M')} - {chat_session['language']} ({chat_session['message_count']} wiadomości)"):
                        if chat_session.get('context'):
                            st.info(f"**Kontekst:** {chat_session['context']}")
                        
                        # Wyświetl wiadomości
                        messages = chat_session['chat_text'].split('\n')
                        for message in messages:
                            if message.strip():
                                if message.startswith('user:'):
                                    st.markdown(f"**👤 Ty:** {message[5:].strip()}")
                                elif message.startswith('assistant:'):
                                    st.markdown(f"**🎓 Korepetytor:** {message[10:].strip()}")
                                st.markdown("---")
                        
                        col_load_chat, col_delete_chat = st.columns([3, 1])
                        with col_load_chat:
                            if st.button(f"💬 Wczytaj tę sesję", key=f"load_chat_session_{i}"):
                                # Wczytaj wiadomości do aktualnego chatu
                                st.session_state.chat_messages = []
                                for message in messages:
                                    if message.strip():
                                        if message.startswith('user:'):
                                            st.session_state.chat_messages.append({
                                                'role': 'user',
                                                'content': message[5:].strip(),
                                                'timestamp': chat_session['timestamp']
                                            })
                                        elif message.startswith('assistant:'):
                                            st.session_state.chat_messages.append({
                                                'role': 'assistant',
                                                'content': message[10:].strip(),
                                                'timestamp': chat_session['timestamp']
                                            })
                                st.session_state.chat_context = chat_session.get('context', '')
                                st.success("✅ Sesja wczytana!")
                                st.rerun()
                        with col_delete_chat:
                            if st.button(f"🗑️ Usuń", key=f"delete_chat_session_{i}"):
                                if db.delete_item(chat_session['id']):
                                    st.success("✅ Sesja usunięta z archiwum!")
                                    st.rerun()
            else:
                st.info("📭 Brak zapisanych sesji czatu w archiwum")
            
            if st.button("❌ Zamknij archiwum", key="close_chat_archive"):
                st.session_state.open_chat_archive = False
                st.rerun()
        
        # 3. SEKCJA CHATU Z KOREPETYTOREM
        elif subsection == "💬 Chat z korepetytorem":
            st.subheader("💬 Chat z korepetytorem")
            st.info("Rozmawiaj z korepetytorem! Ma dostęp do Twoich wskazówek i ćwiczeń.")
            
            # Inicjalizacja historii czatu
            if 'chat_messages' not in st.session_state:
                st.session_state.chat_messages = []
            
            # Kontekst z innych sekcji
            context_info = ""
            if 'chat_context' in st.session_state and st.session_state.chat_context:
                context_info = st.session_state.chat_context
                st.info(f"📋 **Kontekst:** {context_info}")
            
            # Wyświetl historię czatu
            if st.session_state.chat_messages:
                st.markdown("---")
                st.subheader("📚 Historia rozmowy")
                
                for message in st.session_state.chat_messages:
                    if message['role'] == 'user':
                        st.markdown(f"**👤 Ty:** {message['content']}")
                    else:
                        st.markdown(f"**🎓 Korepetytor:** {message['content']}")
                    st.markdown("---")
            
            # Input do chatu
            chat_input = st.text_area(
                "Twoja wiadomość:",
                placeholder=f"Zadaj pytanie o język {target_language}...",
                height=100,
                key="chat_input"
            )
            
            col_send, col_archive_chat, col_clear = st.columns([2, 1, 1])
            
            with col_send:
                if st.button("💬 Wyślij", use_container_width=True, key="send_chat_message"):
                    if chat_input.strip():
                        if tutor_agent:
                            # Dodaj wiadomość użytkownika do historii
                            st.session_state.chat_messages.append({
                                'role': 'user',
                                'content': chat_input,
                                'timestamp': datetime.now()
                            })
                            
                            with st.spinner("Korepetytor pisze..."):
                                try:
                                    # Przygotuj kontekst dla korepetytora
                                    context = ""
                                    if context_info:
                                        context = f"KONTEKST: {context_info}\n\n"
                                    
                                    # Wywołaj korepetytora z kontekstem
                                    answer = tutor_agent.answer_question_with_context(chat_input, target_language, context)
                                    
                                    if answer and "error" not in answer.lower():
                                        # Dodaj odpowiedź korepetytora do historii
                                        st.session_state.chat_messages.append({
                                            'role': 'assistant',
                                            'content': answer,
                                            'timestamp': datetime.now()
                                        })
                                        st.success("✅ Odpowiedź wysłana!")
                                        # Automatycznie zapisz sesję po każdej wiadomości
                                        if len(st.session_state.chat_messages) >= 2:  # Co najmniej pytanie i odpowiedź
                                            db.save_chat_session(st.session_state.chat_messages, target_language, context_info)
                                            # Odśwież dane z bazy danych
                                            reload_data_from_db()
                                        st.rerun()  # Tylko teraz rerun żeby odświeżyć chat
                                    else:
                                        st.error(f"❌ Błąd: {answer}")
                                except Exception as e:
                                    st.error(f"❌ Błąd podczas przetwarzania: {str(e)}")
                        else:
                            st.error("❌ Agent korepetytor nie jest dostępny")
                    else:
                        st.warning("⚠️ Wprowadź wiadomość")
            
            with col_archive_chat:
                if st.button("📚 Archiwum sesji", use_container_width=True, key="show_chat_archive"):
                    st.session_state.open_chat_archive = True
                    st.rerun()
            
            with col_clear:
                if st.button("🗑️ Wyczyść chat", use_container_width=True, key="clear_chat"):
                    st.session_state.chat_messages = []
                    st.session_state.chat_context = ""
                    st.success("✅ Chat wyczyszczony!")
                    st.rerun()
    
    else:
        # Standardowy układ dla innych trybów
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
                
                # Sprawdź czy mamy tekst do analizy z poprzedniego trybu
                default_value = ""
                if "Analiza" in mode and 'analysis_text' in st.session_state and st.session_state.analysis_text:
                    default_value = st.session_state.analysis_text
                    # Pokaż informację o automatycznym wypełnieniu
                    st.success("✅ Tekst został automatycznie wypełniony z poprzedniego trybu!")
                    # NIE czyść tekstu tutaj - zostanie użyty w polu tekstowym
                
                input_text = st.text_area(
                    label,
                    value=default_value,
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
                # Wyczyść analysis_text po użyciu w przycisku
                if 'analysis_text' in st.session_state and st.session_state.analysis_text:
                    st.session_state.analysis_text = ""
                
                if input_text.strip() and len(input_text.strip()) > 3:
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
                        elif "Analiza" in mode:
                            try:
                                analysis = analyze_text(input_text, target_language)
                                if analysis:
                                    # Zapisz do bazy danych
                                    db_id = db.save_correction(
                                        input_text=input_text,
                                        output_text="",  # Analiza nie ma output_text
                                        explanation="",  # Puste explanation dla analiz
                                        language=target_language,
                                        mode='analysis',
                                        analysis_data=analysis  # Przekaż dane analizy
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
                                    st.error("❌ Nie udało się przeanalizować tekstu. Sprawdź czy tekst jest wystarczająco długi.")
                            except Exception as e:
                                st.error(f"❌ Błąd podczas analizy tekstu: {str(e)}")
                                st.info("💡 Sprawdź czy masz wystarczające środki na koncie OpenAI")

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
                    
                    # Przyciski akcji
                    col_copy, col_analyze = st.columns(2)
                    
                    with col_copy:
                        if st.button("📋 Kopiuj tłumaczenie", use_container_width=True, key="copy_latest"):
                            st.write("Skopiowano do schowka!")
                    
                    with col_analyze:
                        if st.button("📊 Przejdź do analizy językowej", use_container_width=True, key="go_to_analysis_translation"):
                            # Oczyść tekst z przedrostków i komentarzy
                            cleaned_text = latest['output']
                            # Usuń przedrostki jak "Tłumaczenie:", "Translation:", etc.
                            prefixes_to_remove = [
                                "Tłumaczenie:", "Translation:", "Przetłumaczony tekst:", 
                                "Translated text:", "Oto tłumaczenie:", "Here's the translation:"
                            ]
                            for prefix in prefixes_to_remove:
                                if cleaned_text.startswith(prefix):
                                    cleaned_text = cleaned_text[len(prefix):].strip()
                            
                            # Zapisz oczyszczony tekst w session state
                            st.session_state.analysis_text = cleaned_text
                            st.session_state.switch_to_analysis = True
                            st.success("✅ Przełączam na tryb analizy językowej...")
                            
                            # Instrukcja dla użytkownika
                            st.info("📋 Przełącz ręcznie na tryb 'Analiza językowa' w menu po lewej stronie.")
                    
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
                    
                    # Przyciski akcji
                    col_copy, col_analyze = st.columns(2)
                    
                    with col_copy:
                        if st.button("📋 Kopiuj poprawiony tekst", use_container_width=True, key="copy_correction"):
                            st.write("Skopiowano do schowka!")
                    
                    with col_analyze:
                        if st.button("📊 Przejdź do analizy językowej", use_container_width=True, key="go_to_analysis"):
                            # Oczyść tekst z przedrostków i komentarzy
                            cleaned_text = latest['output']
                            # Usuń przedrostki jak "Poprawiona wersja:", "Corrected version:", etc.
                            prefixes_to_remove = [
                                "Poprawiona wersja:", "Corrected version:", "Poprawiony tekst:", 
                                "Corrected text:", "Oto poprawiona wersja:", "Here's the corrected version:"
                            ]
                            for prefix in prefixes_to_remove:
                                if cleaned_text.startswith(prefix):
                                    cleaned_text = cleaned_text[len(prefix):].strip()
                            
                            # Zapisz oczyszczony tekst w session state
                            st.session_state.analysis_text = cleaned_text
                            st.session_state.switch_to_analysis = True
                            st.success("✅ Przełączam na tryb analizy językowej...")
                            
                            # Instrukcja dla użytkownika
                            st.info("📋 Przełącz ręcznie na tryb 'Analiza językowa' w menu po lewej stronie.")
                
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
                    if 'analysis_text' in st.session_state and st.session_state.analysis_text:
                        st.info(f"👈 Tekst został automatycznie wypełniony z poprzedniego trybu. Możesz go edytować lub kliknąć 'Analizuj tekst' aby przeanalizować. Historia analiz jest dostępna poniżej.")
                    else:
                        st.info(f"👈 Wprowadź tekst w języku {target_language} i kliknij 'Analizuj tekst' aby zobaczyć analizę z wyjaśnieniami po polsku. Historia analiz jest dostępna poniżej.")
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
                            delete_key = f"delete_translation_{item.get('id', i)}_{i}"
                            
                            if st.button("🗑️", key=delete_key, help="Usuń z bazy danych (natychmiastowe)"):
                                if 'id' in item:
                                    if db.delete_item(item['id']):
                                        st.session_state.translation_history.remove(item)
                                        st.success("✅ Usunięto z bazy danych!")
                                    else:
                                        st.error("❌ Błąd podczas usuwania z bazy danych")
                                else:
                                    # Usuń tylko z sesji jeśli nie ma ID
                                    st.session_state.translation_history.remove(item)
                                    st.success("✅ Usunięto z historii!")
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
        st.markdown("---")
        st.subheader("🔧 Historia poprawek")
        
        # Debugowanie (usuń w produkcji)
        # st.write(f"DEBUG: correction_history length: {len(st.session_state.correction_history)}")
        # correction_items = [item for item in st.session_state.correction_history if item.get('mode') == 'correction']
        # st.write(f"DEBUG: correction items found: {len(correction_items)}")
        
        if st.session_state.correction_history:
            # Filtruj tylko poprawki i weź ostatnie 5
            correction_items = [item for item in st.session_state.correction_history if item.get('mode') == 'correction']
            for i, item in enumerate(reversed(correction_items[-5:])):
                    with st.expander(f"Poprawka {len(st.session_state.correction_history) - i} - {item['timestamp'].strftime('%H:%M:%S')}"):
                        # Przycisk usuwania
                        col_delete, col_content = st.columns([1, 10])
                        with col_delete:
                            delete_key = f"delete_correction_{item.get('id', i)}_{i}"
                            
                            if st.button("🗑️", key=delete_key, help="Usuń z bazy danych (natychmiastowe)"):
                                if 'id' in item:
                                    if db.delete_item(item['id']):
                                        st.session_state.correction_history.remove(item)
                                        st.success("✅ Usunięto z bazy danych!")
                                    else:
                                        st.error("❌ Błąd podczas usuwania z bazy danych")
                                else:
                                    # Usuń tylko z sesji jeśli nie ma ID
                                    st.session_state.correction_history.remove(item)
                                    st.success("✅ Usunięto z historii!")
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
        st.markdown("---")
        st.subheader("📊 Historia analiz")
        
        # Debugowanie (usuń w produkcji)
        # st.write(f"DEBUG: correction_history length: {len(st.session_state.correction_history)}")
        # analysis_items = [item for item in st.session_state.correction_history if item.get('mode') == 'analysis']
        # st.write(f"DEBUG: analysis items found: {len(analysis_items)}")
        
        if st.session_state.correction_history:
            # Filtruj tylko analizy i weź ostatnie 5
            analysis_items = [item for item in st.session_state.correction_history if item.get('mode') == 'analysis']
            for i, item in enumerate(reversed(analysis_items[-5:])):
                    with st.expander(f"Analiza {len(st.session_state.correction_history) - i} - {item['timestamp'].strftime('%H:%M:%S')}"):
                        # Przycisk usuwania
                        col_delete, col_content = st.columns([1, 10])
                        with col_delete:
                            delete_key = f"delete_analysis_{item.get('id', i)}_{i}"
                            
                            if st.button("🗑️", key=delete_key, help="Usuń z bazy danych (natychmiastowe)"):
                                if 'id' in item:
                                    if db.delete_item(item['id']):
                                        st.session_state.correction_history.remove(item)
                                        st.success("✅ Usunięto z bazy danych!")
                                    else:
                                        st.error("❌ Błąd podczas usuwania z bazy danych")
                                else:
                                    # Usuń tylko z sesji jeśli nie ma ID
                                    st.session_state.correction_history.remove(item)
                                    st.success("✅ Usunięto z historii!")
                        with col_content:
                            st.markdown("**Analizowany tekst:**")
                            st.write(item['input'])
                            st.markdown(f"**Język:** {item['language']}")
                            
                            # Wyświetl analizę jeśli jest dostępna
                            if 'analysis' in item and item['analysis']:
                                analysis = item['analysis']
                                
                                # Słownictwo
                                if hasattr(analysis, 'vocabulary_items') and analysis.vocabulary_items:
                                    st.markdown("**📚 Słownictwo:**")
                                    for vocab_item in analysis.vocabulary_items[:3]:  # Pokaż więcej elementów
                                        st.markdown(f"**• {vocab_item.word}** - {vocab_item.translation}")
                                        st.write(f"  Część mowy: {vocab_item.part_of_speech}")
                                        st.write(f"  Przykład: {vocab_item.example_sentence}")
                                        st.write(f"  Poziom: {vocab_item.difficulty_level}")
                                        st.markdown("---")
                                
                                # Reguły gramatyczne
                                if hasattr(analysis, 'grammar_rules') and analysis.grammar_rules:
                                    st.markdown("**📖 Reguły gramatyczne:**")
                                    for rule in analysis.grammar_rules[:2]:  # Pokaż więcej reguł
                                        st.markdown(f"**• {rule.rule_name}**")
                                        st.write(f"  Wyjaśnienie: {rule.explanation}")
                                        st.write("  Przykłady:")
                                        for example in rule.examples[:3]:
                                            st.write(f"    - {example}")
                                        st.write(f"  Poziom: {rule.difficulty_level}")
                                        st.markdown("---")
                                
                                # Wskazówki do nauki
                                if hasattr(analysis, 'learning_tips') and analysis.learning_tips:
                                    st.markdown("**💡 Wskazówki do nauki:**")
                                    for tip in analysis.learning_tips[:3]:  # Pokaż więcej wskazówek
                                        st.write(f"• {tip}")
                            else:
                                st.info("📊 Analiza nie jest dostępna dla tego wpisu")
    

    
    # Odśwież dane z bazy danych na końcu
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    elif (datetime.now() - st.session_state.last_refresh).seconds > 30:  # Odśwież co 30 sekund
        reload_data_from_db()
        st.session_state.last_refresh = datetime.now()

if __name__ == "__main__":
    main()
