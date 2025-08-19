# Instrukcje konfiguracji i uruchomienia

## 1. Konfiguracja środowiska

### Opcja A: Używając conda (zalecane)
```bash
# Aktywuj środowisko conda
conda activate od_zera_do_ai

# Dodaj kanał conda-forge
conda config --append channels conda-forge

# Zainstaluj zależności
conda install -y streamlit ffmpeg pydub openai==1.47.0 python-dotenv

# Zainstaluj instructor przez pip
pip install instructor
```

### Opcja B: Używając pip
```bash
# Zainstaluj wszystkie zależności
pip install -r requirements.txt

# Dodatkowo zainstaluj ffmpeg (na macOS)
brew install ffmpeg

# Lub na Ubuntu/Debian
sudo apt-get install ffmpeg
```

## 2. Konfiguracja środowiska

### 2.1 Klucz API OpenAI

1. Skopiuj plik z przykładową konfiguracją:
```bash
cp env_example.txt .env
```

2. Edytuj plik `.env` i dodaj swój klucz API OpenAI:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

3. Aby uzyskać klucz API OpenAI:
   - Przejdź do https://platform.openai.com/
   - Zaloguj się lub utwórz konto
   - Przejdź do sekcji "API Keys"
   - Utwórz nowy klucz API
   - Skopiuj klucz i wklej go do pliku `.env`

### 2.2 Baza danych Qdrant

1. **Instalacja Qdrant:**
   ```bash
   # Używając Docker (zalecane)
   docker run -p 6333:6333 qdrant/qdrant
   
   # Lub używając pip
   pip install qdrant-client
   ```

2. **Konfiguracja w pliku .env:**
   ```
   QDRANT_URL=http://localhost:6333
   QDRANT_API_KEY=your_qdrant_api_key_here
   QDRANT_COLLECTION_NAME=language_helper_history
   ```

3. **Uruchomienie Qdrant:**
   - Jeśli używasz Docker, Qdrant będzie dostępny pod adresem http://localhost:6333
   - Możesz sprawdzić status pod adresem http://localhost:6333/collections

## 3. Uruchomienie aplikacji

```bash
# Uruchom aplikację
streamlit run app.py
```

Aplikacja będzie dostępna pod adresem: http://localhost:8501

## 4. Obsługiwane formaty plików

Aplikacja obsługuje wczytywanie tekstu z następujących formatów:

### 📄 Pliki tekstowe (.txt)
- Obsługuje różne kodowania: UTF-8, CP1250, ISO-8859-2, Latin-1
- Automatyczna detekcja kodowania
- Maksymalny rozmiar: 10MB

### 📝 Dokumenty Word (.docx)
- Obsługuje dokumenty Microsoft Word
- Wyciąga tekst z wszystkich paragrafów
- Zachowuje strukturę tekstu

### 📋 Dokumenty PDF (.pdf)
- Obsługuje dokumenty PDF
- Wyciąga tekst ze wszystkich stron
- Automatyczne łączenie tekstu z różnych stron

### ⚠️ Ograniczenia
- Maksymalny rozmiar pliku: 10MB
- Pliki PDF muszą zawierać tekst (nie obrazy)
- Pliki DOCX muszą być w formacie .docx (nie .doc)

## 5. Funkcjonalności aplikacji

### 🔄 Przełączanie trybów pracy
- **Automatyczne czyszczenie** - Historia jest czyszczona automatycznie przy zmianie trybu
- **Wskaźnik trybu** - Aktualny tryb jest wyświetlany w kolumnie wyników
- **Przycisk czyszczenia** - Możliwość ręcznego wyczyszczenia historii
- **Kontekstowe komunikaty** - Różne komunikaty dla każdego trybu

### Tłumaczenie (PL → EN)
- Wybierz sposób wprowadzania tekstu:
  - **Ręczne wpisywanie** - wpisz tekst bezpośrednio
  - **Wczytanie z pliku** - wybierz plik TXT, DOCX lub PDF
- Wybierz język docelowy
- Kliknij "Przetłumacz"
- Otrzymasz przetłumaczony tekst

### Tłumaczenie (PL → Wybrany język)
- Wybierz tryb "Tłumaczenie (PL → Wybrany język)"
- Wybierz sposób wprowadzania tekstu (ręcznie lub z pliku)
- Wybierz język docelowy z listy
- Wpisz tekst i przetłumacz

### Poprawianie tekstu
- Wybierz sposób wprowadzania tekstu (ręcznie lub z pliku)
- Wpisz tekst w języku obcym z błędami
- Kliknij "Popraw tekst"
- Otrzymasz poprawiony tekst z wyjaśnieniami po polsku
- Wybierz tryb "Poprawianie tekstu"
- Wybierz język tekstu do poprawienia
- Wpisz tekst z błędami
- Otrzymasz poprawioną wersję z wyjaśnieniami

### Analiza językowa
- Wybierz sposób wprowadzania tekstu (ręcznie lub z pliku)
- Wpisz tekst w języku obcym do analizy
- Kliknij "Analizuj tekst"
- Otrzymasz analizę słownictwa i gramatyki z wyjaśnieniami po polsku
- Wybierz tryb "Analiza językowa"
- Wpisz tekst do analizy
- Otrzymasz:
  - Listę słownictwa z wyjaśnieniami
  - Reguły gramatyczne
  - Wskazówki do nauki

### Generowanie audio
- **Automatyczne generowanie** - Audio jest generowane automatycznie dla każdego tłumaczenia
- **Historia audio** - Audio jest zapisywane w historii i dostępne nawet po przejściu do historii
- **Odtwarzanie** - Kliknij przycisk play w odtwarzaczu audio
- **Pobieranie** - Użyj przycisku "📥 Pobierz audio" aby zapisać plik lokalnie
- **Różne głosy** - Automatyczne mapowanie głosów dla różnych języków

### 💾 Baza danych Qdrant
- **Trwałe przechowywanie** - Wszystkie tłumaczenia i poprawki są zapisywane w bazie danych
- **Automatyczne ładowanie** - Historia jest automatycznie ładowana przy uruchomieniu aplikacji
- **Odświeżanie historii** - Przycisk "🔄 Odśwież" do ponownego ładowania z bazy danych
- **Przełączanie trybów** - Historia jest automatycznie odświeżana przy zmianie trybu pracy
- **Statystyki** - Liczba rekordów i status bazy danych w sidebarze
- **Usuwanie elementów** - Możliwość usuwania pojedynczych elementów z historii
- **Czyszczenie bazy** - Przycisk "🗑️ Wyczyść" do wyczyszczenia całej bazy danych

## 5. Rozwiązywanie problemów

### Błąd: "No module named 'instructor'"
```bash
pip install instructor
```

### Błąd: "OPENAI_API_KEY environment variable"
- Sprawdź czy plik `.env` istnieje
- Sprawdź czy klucz API jest poprawny
- Uruchom ponownie aplikację

### Błąd: "You tried to access openai.ChatCompletion"
Ten błąd został już naprawiony w kodzie. Aplikacja używa nowej składni OpenAI API (v1.0+). Jeśli nadal widzisz ten błąd:
- Upewnij się, że masz najnowszą wersję kodu
- Sprawdź czy wszystkie pliki zostały zaktualizowane

### Błąd podczas generowania audio

#### Najczęstsze przyczyny:
1. **Brak środków na koncie OpenAI** - Sprawdź saldo na https://platform.openai.com/account/billing
2. **Nieprawidłowy klucz API** - Sprawdź czy klucz w pliku .env jest poprawny
3. **Tekst za długi** - Maksymalna długość to 4000 znaków (automatycznie przycinane)
4. **Brak połączenia z internetem** - Sprawdź połączenie sieciowe

#### Rozwiązania:
```bash
# Sprawdź czy ffmpeg jest zainstalowany
which ffmpeg

# Sprawdź klucz API
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', 'OK' if os.getenv('OPENAI_API_KEY') else 'MISSING')"

# Test funkcji audio
python test_audio.py
```

#### Problem z odtwarzaniem audio:
- **Format WAV** - Aplikacja używa formatu WAV zamiast MP3 dla lepszej kompatybilności
- **Pobieranie pliku** - Jeśli odtwarzacz nie działa, pobierz plik i odtwórz lokalnie
- **Przeglądarka** - Sprawdź czy przeglądarka obsługuje format WAV
- **Rozmiar pliku** - Sprawdź czy plik audio ma rozmiar > 1000 bajtów

#### Problem z bazą danych Qdrant:
- **Błąd "Connection refused"** - Upewnij się, że Qdrant jest uruchomiony na porcie 6333
- **Sprawdź status Qdrant** - Przejdź do http://localhost:6333/collections
- **Uruchom Qdrant** - `docker run -p 6333:6333 qdrant/qdrant`
- **Sprawdź konfigurację** - Upewnij się, że zmienne QDRANT_* są ustawione w pliku .env

#### Problem z historią:
- **Historia nie wyświetla się** - Użyj przycisku "🔄 Odśwież" w sidebarze
- **Historia znika po zmianie trybu** - Historia jest automatycznie odświeżana przy zmianie trybu
- **Brak rekordów z poprzednich sesji** - Sprawdź czy baza danych Qdrant jest uruchomiona
- **Ręczne odświeżanie** - Kliknij "🔄 Odśwież" aby ponownie załadować dane z bazy

#### Limity OpenAI TTS:
- Maksymalna długość tekstu: 4096 znaków
- Obsługiwane głosy: alloy, echo, fable, onyx, nova, shimmer
- Format wyjściowy: WAV (lepsza kompatybilność z przeglądarkami)

### Aplikacja nie uruchamia się
- Sprawdź czy wszystkie zależności są zainstalowane
- Sprawdź czy port 8501 jest wolny
- Spróbuj uruchomić z innym portem: `streamlit run app.py --server.port 8502`

## 6. Struktura projektu

```
projekt-zaliczeniowy/
├── app.py                 # Główna aplikacja Streamlit
├── text_corrector.py      # Moduł poprawiania tekstów
├── grammar_helper.py      # Moduł analizy językowej
├── audio_generator.py     # Moduł generowania audio
├── requirements.txt       # Zależności Python
├── .env                   # Zmienne środowiskowe (utworzyć)
├── env_example.txt        # Przykład konfiguracji
├── README.md              # Dokumentacja projektu
├── SETUP.md               # Ten plik
└── .gitignore             # Pliki do ignorowania przez git
```

## 7. Wersje funkcjonalności

- **v1**: ✅ Tłumaczenie z polskiego na angielski
- **v2**: ✅ Tłumaczenie na wybrane języki
- **v3**: ✅ Poprawianie błędów w tekstach obcojęzycznych
- **v4**: ✅ Ulepszone formatowanie wyników
- **v5**: ✅ Wyjaśnienia słów i gramatyki
- **v6**: ✅ Generowanie audio
- **v7**: ✅ Historia w bazie danych Qdrant
