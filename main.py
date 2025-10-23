#!/usr/bin/env python3
"""
Music Genre Sorter - Główny plik aplikacji
Aplikacja do automatycznego sortowania muzyki elektronicznej według gatunków
"""

import sys
import logging
from pathlib import Path

# Dodanie ścieżki projektu do sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import LOG_LEVEL, LOG_FORMAT
from gui import MusicGenreSorterGUI

def setup_logging():
    """Konfiguruje system logowania"""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler('music_sorter.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Główna funkcja aplikacji"""
    try:
        # Konfiguracja logowania
        setup_logging()
        logger = logging.getLogger(__name__)
        
        logger.info("Uruchamianie Music Genre Sorter...")
        
        # Sprawdzenie wymaganych bibliotek
        try:
            import tkinter
            import mutagen
            import requests
        except ImportError as e:
            logger.error(f"Brak wymaganej biblioteki: {e}")
            print(f"Błąd: Brak wymaganej biblioteki: {e}")
            print("Zainstaluj wymagane biblioteki używając: pip install -r requirements.txt")
            sys.exit(1)
        
        # Uruchomienie GUI
        app = MusicGenreSorterGUI()
        app.run()
        
    except KeyboardInterrupt:
        print("\\nAplikacja przerwana przez użytkownika")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Nieoczekiwany błąd: {e}", exc_info=True)
        print(f"Wystąpił nieoczekiwany błąd: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()