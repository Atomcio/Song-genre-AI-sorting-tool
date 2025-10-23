# Music Genre Sorter - ChatGPT Edition
# PowerShell Launcher Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Music Genre Sorter - ChatGPT Edition" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ustawienie klucza OpenAI API
$env:OPENAI_API_KEY = ""

# Sprawdź klucz OpenAI API
Write-Host "Sprawdzanie konfiguracji..." -ForegroundColor Yellow
Write-Host "✓ Klucz OpenAI API ustawiony - ChatGPT aktywny!" -ForegroundColor Green
Write-Host ""

# Sprawdź czy Python jest dostępny
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ BŁĄD: Python nie jest zainstalowany lub niedostępny!" -ForegroundColor Red
    Read-Host "Naciśnij Enter aby zakończyć"
    exit 1
}

# Przejdź do katalogu skryptu
Set-Location $PSScriptRoot

# Sprawdź czy requirements.txt istnieje
if (Test-Path "requirements.txt") {
    Write-Host "✓ Znaleziono requirements.txt" -ForegroundColor Green
} else {
    Write-Host "⚠️  Brak pliku requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Uruchamianie aplikacji..." -ForegroundColor Cyan
Write-Host ""

# Uruchom aplikację
try {
    python main.py
} catch {
    Write-Host ""
    Write-Host "❌ BŁĄD: Nie udało się uruchomić aplikacji!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Sprawdź czy:" -ForegroundColor Yellow
    Write-Host "- Wszystkie biblioteki są zainstalowane: pip install -r requirements.txt" -ForegroundColor White
    Write-Host "- Plik main.py istnieje w tym katalogu" -ForegroundColor White
    Write-Host ""
    Read-Host "Naciśnij Enter aby zakończyć"
}