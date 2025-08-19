# Pomocnik Językowy - Language Learning Assistant

Aplikacja do nauki języków obcych wykorzystująca AI do tłumaczenia, poprawiania tekstów i generowania audio.

## Funkcjonalności

- Tłumaczenie tekstów z polskiego na wybrane języki
- Poprawianie błędów gramatycznych w tekstach obcojęzycznych
- Generowanie wyjaśnień słów i konstrukcji gramatycznych
- Generowanie wersji audio dla nauki wymowy
- Historia tłumaczeń i poprawek
- Wczytywanie tekstu z plików (TXT, DOCX, PDF)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone <repository-url>
cd projekt-zaliczeniowy
```

2. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

3. Skonfiguruj zmienne środowiskowe:
```bash
cp env_example.txt .env
```
Następnie edytuj plik `.env` i dodaj swój klucz API OpenAI.

4. Uruchom aplikację:
```bash
streamlit run app.py
```

## Użycie

1. Otwórz przeglądarkę i przejdź do `http://localhost:8501`
2. Wybierz tryb pracy (tłumaczenie, poprawianie lub analiza)
3. Wybierz sposób wprowadzania tekstu:
   - **Ręczne wpisywanie** - wpisz tekst bezpośrednio
   - **Wczytanie z pliku** - wybierz plik TXT, DOCX lub PDF
4. Wybierz język docelowy (dla tłumaczenia)
5. Kliknij odpowiedni przycisk akcji
6. Obejrzyj wyniki i wyjaśnienia
7. Opcjonalnie wygeneruj wersję audio

## Obsługiwane formaty plików

Aplikacja obsługuje wczytywanie tekstu z następujących formatów:

- **TXT** - Pliki tekstowe (UTF-8, CP1250, ISO-8859-2, Latin-1)
- **DOCX** - Dokumenty Microsoft Word
- **PDF** - Dokumenty PDF

**Maksymalny rozmiar pliku:** 10MB

## Wersje

- **v1**: Tłumaczenie z polskiego na angielski
- **v2**: Tłumaczenie na wybrane języki
- **v3**: Poprawianie błędów w tekstach obcojęzycznych
- **v4**: Ulepszone formatowanie wyników
- **v5**: Wyjaśnienia słów i gramatyki
- **v6**: Generowanie audio
- **v7**: Historia w bazie danych
- **v8**: Wczytywanie tekstu z plików (TXT, DOCX, PDF)
