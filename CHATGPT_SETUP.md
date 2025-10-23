# Konfiguracja ChatGPT API

## Wprowadzenie

Aplikacja Music Genre Sorter została rozszerzona o integrację z ChatGPT API, która zapewnia znacznie dokładniejszą klasyfikację gatunków muzycznych. ChatGPT analizuje każdy utwór na podstawie nazwy artysty, tytułu i nazwy pliku, dostarczając szczegółowe informacje o gatunku, podgatunku i charakterystykach utworu.

## Jak uzyskać klucz OpenAI API

1. **Zarejestruj się na OpenAI**
   - Przejdź na stronę: https://platform.openai.com/
   - Utwórz konto lub zaloguj się

2. **Uzyskaj klucz API**
   - Przejdź do sekcji "API Keys"
   - Kliknij "Create new secret key"
   - Skopiuj wygenerowany klucz (zaczyna się od `sk-`)

3. **Dodaj środki do konta**
   - Przejdź do "Billing" 
   - Dodaj kartę płatniczą i środki (minimum $5)
   - ChatGPT API jest płatne, ale bardzo tanie (~$0.002 za 1000 tokenów)

## Konfiguracja w aplikacji

### Opcja 1: Zmienna środowiskowa (zalecane)

1. **Windows:**
   ```cmd
   setx OPENAI_API_KEY "twój_klucz_api_tutaj"
   ```

2. **Uruchom ponownie terminal/aplikację**

### Opcja 2: Plik .env

1. **Utwórz plik `.env` w folderze aplikacji:**
   ```
   OPENAI_API_KEY=twój_klucz_api_tutaj
   ```

2. **Uruchom ponownie aplikację**

## Weryfikacja konfiguracji

Po poprawnej konfiguracji, w logach aplikacji powinieneś zobaczyć:
```
INFO:web_searcher:OpenAI API zainicjalizowane
```

Zamiast:
```
WARNING:web_searcher:Brak klucza OpenAI API - funkcje ChatGPT będą wyłączone
```

## Jak działa ChatGPT w aplikacji

1. **Automatyczna analiza**: ChatGPT analizuje każdy utwór automatycznie podczas klasyfikacji
2. **Szczegółowe informacje**: Otrzymujesz główny gatunek, podgatunek, poziom pewności i tagi
3. **Specjalizacja**: ChatGPT jest szczególnie dobry w rozpoznawaniu niszowych gatunków elektronicznych
4. **Fallback**: Jeśli ChatGPT nie jest dostępny, aplikacja używa innych metod klasyfikacji

## Koszty

- **ChatGPT-3.5-turbo**: ~$0.002 za 1000 tokenów
- **Średni koszt na utwór**: ~$0.001-0.002 (bardzo tanie)
- **1000 utworów**: ~$1-2

## Rozwiązywanie problemów

### Błąd: "Invalid API key"
- Sprawdź czy klucz jest poprawny
- Upewnij się, że zaczyna się od `sk-`
- Sprawdź czy masz środki na koncie OpenAI

### Błąd: "Rate limit exceeded"
- Poczekaj chwilę i spróbuj ponownie
- Rozważ upgrade planu na OpenAI

### ChatGPT nie działa
- Sprawdź połączenie internetowe
- Sprawdź status OpenAI API: https://status.openai.com/

## Bezpieczeństwo

- **NIE** udostępniaj swojego klucza API
- **NIE** commituj klucza do repozytorium
- Używaj zmiennych środowiskowych lub pliku .env
- Regularnie rotuj klucze API