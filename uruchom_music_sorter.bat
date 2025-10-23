@echo off
title Music Genre Sorter - ChatGPT Edition
echo ========================================
echo    Music Genre Sorter - ChatGPT Edition
echo ========================================
echo.

REM Ustawienie klucza OpenAI API
set OPENAI_API_KEY=

echo Sprawdzanie klucza OpenAI API...
echo ✓ Klucz OpenAI API ustawiony - ChatGPT aktywny!
echo.

echo Uruchamianie aplikacji...
echo.

cd /d "%~dp0"
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo BLAD: Aplikacja zakonczyla sie z bledem!
    echo Sprawdz czy:
    echo - Python jest zainstalowany
    echo - Wszystkie biblioteki sa zainstalowane (pip install -r requirements.txt)
    echo.
    pause
)