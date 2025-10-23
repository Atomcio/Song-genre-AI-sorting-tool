# 🎵 Music Genre Sorter - Instrukcje Uruchamiania

## 🚀 Sposoby uruchamiania aplikacji

### 1. **Najłatwiejszy sposób - Plik .bat**
```
Kliknij dwukrotnie: uruchom_music_sorter.bat
```
- Automatycznie sprawdza konfigurację
- Wyświetla status ChatGPT
- Uruchamia aplikację

### 2. **PowerShell (zaawansowany)**
```
Kliknij prawym przyciskiem: uruchom_music_sorter.ps1 → "Uruchom z PowerShell"
```
- Kolorowe komunikaty
- Szczegółowe sprawdzanie systemu
- Lepsze komunikaty o błędach

### 3. **Skrót na pulpicie**
```
Kliknij dwukrotnie: utworz_skrot_pulpit.vbs
```
- Tworzy skrót na pulpicie
- Jednorazowe uruchomienie
- Potem używaj skrótu z pulpitu

### 4. **Ręczne uruchomienie**
```bash
cd "ścieżka_do_folderu"
python main.py
```

## ⚙️ Wymagania

### Przed pierwszym uruchomieniem:
1. **Python 3.8+** zainstalowany
2. **Zainstalowane biblioteki:**
   ```bash
   pip install -r requirements.txt
   ```

### Dla ChatGPT (opcjonalne):
1. **Klucz OpenAI API** z https://platform.openai.com/api-keys
2. **Ustaw zmienną środowiskową:**
   ```bash
   set OPENAI_API_KEY=twoj_klucz_api
   ```

## 🔧 Rozwiązywanie problemów

### Aplikacja się nie uruchamia:
- Sprawdź czy Python jest zainstalowany: `python --version`
- Zainstaluj biblioteki: `pip install -r requirements.txt`
- Sprawdź czy jesteś w odpowiednim folderze

### ChatGPT nie działa:
- Sprawdź klucz API: `echo %OPENAI_API_KEY%`
- Upewnij się że klucz jest poprawny
- **Sprawdź saldo konta OpenAI** - najczęstszy problem!

### ⚠️ Błąd "insufficient_quota" (brak środków):
**Problem:** `Error code: 429 - insufficient_quota`
**Rozwiązanie:**
1. Przejdź do https://platform.openai.com/account/billing
2. Dodaj metodę płatności (karta kredytowa)
3. Doładuj konto (minimum $5-10)
4. Uruchom aplikację ponownie

**Uwaga:** Aplikacja będzie działać bez ChatGPT w trybie podstawowym!

### Błędy podczas analizy:
- Sprawdź połączenie internetowe
- Upewnij się że pliki muzyczne są dostępne
- Sprawdź logi w pliku `music_sorter.log`

## 📁 Struktura plików

```
📁 music_genre_sorter/
├── 🚀 uruchom_music_sorter.bat     # Główny launcher
├── 🚀 uruchom_music_sorter.ps1     # PowerShell launcher  
├── 🔗 utworz_skrot_pulpit.vbs      # Tworzenie skrótu
├── 📖 INSTRUKCJE_URUCHAMIANIA.md   # Ten plik
├── ⚙️ CHATGPT_SETUP.md             # Konfiguracja ChatGPT
└── 🎵 main.py                      # Główna aplikacja
```

## 🎯 Pierwsze uruchomienie

1. **Kliknij:** `uruchom_music_sorter.bat`
2. **Przeczytaj** komunikaty o konfiguracji
3. **Ustaw klucz ChatGPT** (jeśli chcesz)
4. **Wybierz folder** z muzyką
5. **Rozpocznij analizę!**

---
*Music Genre Sorter - ChatGPT Edition* 🎵✨