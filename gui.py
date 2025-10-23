"""
Interfejs graficzny dla Music Genre Sorter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser
import re
import threading
import queue
from pathlib import Path
import json
from datetime import datetime
import os

from metadata_analyzer import MetadataAnalyzer
from web_searcher import WebSearcher
from genre_classifier import GenreClassifier
from file_organizer import FileOrganizer
from config import WINDOW_SIZE, THEME, DEFAULT_MUSIC_DIR, DEFAULT_OUTPUT_DIR

class MusicGenreSorterGUI:
    """Główna klasa interfejsu graficznego"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Music Genre Sorter - Sortowanie muzyki elektronicznej")
        self.root.geometry(WINDOW_SIZE)
        
        # Komponenty aplikacji
        self.metadata_analyzer = MetadataAnalyzer()
        # Wczytaj zapisane klucze API do zmiennych środowiskowych zanim zainicjalizujemy integracje
        self._load_saved_api_keys()
        self.web_searcher = WebSearcher()
        self.genre_classifier = GenreClassifier()
        self.file_organizer = FileOrganizer()
        
        # Zmienne
        self.source_dir = tk.StringVar(value=str(DEFAULT_MUSIC_DIR))
        self.output_dir = tk.StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.recursive_scan = tk.BooleanVar(value=True)
        self.use_web_search = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=False)
        self.min_confidence = tk.DoubleVar(value=0.5)
        
        # Dane
        self.music_files = []
        self.classifications = []
        self.current_analysis = None
        
        # Queue dla komunikacji z wątkami
        self.progress_queue = queue.Queue()

        # Bufor uzasadnień AI i rotacja co 30s
        self.ai_reasons_cache = []  # list[str]
        self._current_ai_text = ""
        self._rotation_job = None
        # Identyfikatory animacji
        self._fade_in_job = None
        self._fade_out_job = None
        self._swap_job = None
        
        self.setup_ui()
        self.setup_styles()
        
        # Sprawdź status ChatGPT po utworzeniu UI
        self.check_chatgpt_status()
        
    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        # Główny notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Zakładki
        self.setup_main_tab()
        self.setup_settings_tab()
        self.setup_results_tab()
        self.setup_logs_tab()
        
    def setup_main_tab(self):
        """Konfiguruje główną zakładkę"""
        main_frame = ttk.Frame(self.notebook)
        self.notebook.add(main_frame, text="Główne")
        
        # Sekcja wyboru katalogów
        dirs_frame = ttk.LabelFrame(main_frame, text="Katalogi", padding=10)
        dirs_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Katalog źródłowy
        ttk.Label(dirs_frame, text="Katalog z muzyką:").grid(row=0, column=0, sticky=tk.W, pady=2)
        source_frame = ttk.Frame(dirs_frame)
        source_frame.grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        source_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(source_frame, textvariable=self.source_dir).grid(row=0, column=0, sticky=tk.EW)
        ttk.Button(source_frame, text="Przeglądaj", 
                  command=self.browse_source_dir).grid(row=0, column=1, padx=(5, 0))
        
        # Katalog docelowy
        ttk.Label(dirs_frame, text="Katalog docelowy:").grid(row=1, column=0, sticky=tk.W, pady=2)
        output_frame = ttk.Frame(dirs_frame)
        output_frame.grid(row=1, column=1, sticky=tk.EW, padx=(10, 0), pady=2)
        output_frame.columnconfigure(0, weight=1)
        
        ttk.Entry(output_frame, textvariable=self.output_dir).grid(row=0, column=0, sticky=tk.EW)
        ttk.Button(output_frame, text="Przeglądaj", 
                  command=self.browse_output_dir).grid(row=0, column=1, padx=(5, 0))
        
        dirs_frame.columnconfigure(1, weight=1)
        
        # Opcje skanowania
        options_frame = ttk.LabelFrame(main_frame, text="Opcje", padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(options_frame, text="Skanuj podkatalogi", 
                       variable=self.recursive_scan).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Wyszukuj informacje w internecie", 
                       variable=self.use_web_search).pack(anchor=tk.W)
        ttk.Checkbutton(options_frame, text="Tryb testowy (nie przenoś plików)", 
                       variable=self.dry_run).pack(anchor=tk.W)
        
        # Minimalny poziom pewności
        conf_frame = ttk.Frame(options_frame)
        conf_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(conf_frame, text="Minimalny poziom pewności:").pack(side=tk.LEFT)
        ttk.Scale(conf_frame, from_=0.0, to=1.0, variable=self.min_confidence, 
                 orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Label(conf_frame, textvariable=self.min_confidence).pack(side=tk.LEFT)
        
        # Przyciski akcji
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(buttons_frame, text="1. Skanuj pliki", 
                  command=self.scan_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="2. Analizuj i klasyfikuj", 
                  command=self.analyze_files).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="3. Sortuj pliki", 
                  command=self.sort_files).pack(side=tk.LEFT, padx=(0, 5))
        
        # Pasek postępu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Status
        self.status_var = tk.StringVar(value="Gotowy do pracy")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W)

        # Panel uzasadnienia AI – wielowierszowy (3 linie), pełny opis
        self.ai_panel_frame = ttk.LabelFrame(main_frame, text="Analiza AI – uzasadnienie klasyfikacji", padding=6)
        self.ai_panel_frame.pack(fill=tk.X, pady=(5, 10))
        self.ai_reason_label = tk.Text(self.ai_panel_frame, height=3, wrap=tk.WORD)
        self.ai_reason_label.configure(state=tk.DISABLED, relief=tk.FLAT, bg="#ffffff", fg="#000000", insertbackground="#000000")
        self.ai_reason_label.pack(fill=tk.X)
        
    def setup_settings_tab(self):
        """Konfiguruje zakładkę ustawień"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Ustawienia")
        
        # API Keys
        api_frame = ttk.LabelFrame(settings_frame, text="Klucze API", padding=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="Spotify Client ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.spotify_id_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.spotify_id_var, width=50).grid(row=0, column=1, sticky=tk.EW, padx=(10, 0))
        
        ttk.Label(api_frame, text="Spotify Client Secret:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.spotify_secret_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.spotify_secret_var, width=50, show="*").grid(row=1, column=1, sticky=tk.EW, padx=(10, 0))
        
        ttk.Label(api_frame, text="Last.fm API Key:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.lastfm_key_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.lastfm_key_var, width=50).grid(row=2, column=1, sticky=tk.EW, padx=(10, 0))

        ttk.Label(api_frame, text="OpenAI API Key:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.openai_key_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.openai_key_var, width=50, show="*").grid(row=3, column=1, sticky=tk.EW, padx=(10, 0))
        ttk.Button(api_frame, text="Zapisz klucze", command=self.save_user_settings).grid(row=4, column=1, sticky=tk.E, pady=(5, 0))
        
        api_frame.columnconfigure(1, weight=1)

        # Motyw (light/dark)
        theme_frame = ttk.LabelFrame(settings_frame, text="Motyw aplikacji", padding=10)
        theme_frame.pack(fill=tk.X, pady=(0, 10))
        # Wymuś domyślnie pełny ciemny motyw
        self.theme_var = tk.StringVar(value="dark")
        ttk.Radiobutton(theme_frame, text="Jasny", value="light", variable=self.theme_var, command=self.apply_theme).pack(side=tk.LEFT)
        ttk.Radiobutton(theme_frame, text="Czarny (Dark)", value="dark", variable=self.theme_var, command=self.apply_theme).pack(side=tk.LEFT, padx=(10,0))
        ttk.Button(theme_frame, text="Dostrój kolory…", command=self.open_color_options_dialog).pack(side=tk.LEFT, padx=(10,0))
        # Zastosuj motyw po utworzeniu przełącznika
        self.apply_theme()
        # Wczytaj zapisane ustawienia API (jeśli istnieją)
        self.load_user_settings()

        # Opcje organizacji plików
        file_options_frame = ttk.LabelFrame(settings_frame, text="Opcje organizacji plików", padding=10)
        file_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.use_pretty_names = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_options_frame, text="Używaj ładnych nazw plików (Wykonawca - Tytuł (Rok))", 
                       variable=self.use_pretty_names).pack(anchor=tk.W)
        
        self.copy_files = tk.BooleanVar(value=True)
        ttk.Checkbutton(file_options_frame, text="Kopiuj pliki (zamiast przenosić oryginały)", 
                       variable=self.copy_files).pack(anchor=tk.W, pady=(5, 0))
        
        # Gatunki
        genres_frame = ttk.LabelFrame(settings_frame, text="Konfiguracja gatunków", padding=10)
        genres_frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista gatunków
        genres_list_frame = ttk.Frame(genres_frame)
        genres_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.genres_tree = ttk.Treeview(genres_list_frame, columns=("folder",), show="tree headings")
        self.genres_tree.heading("#0", text="Gatunek")
        self.genres_tree.heading("folder", text="Folder docelowy")
        self.genres_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        genres_scroll = ttk.Scrollbar(genres_list_frame, orient=tk.VERTICAL, command=self.genres_tree.yview)
        genres_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.genres_tree.configure(yscrollcommand=genres_scroll.set)
        
        self.populate_genres_tree()
        
    def setup_results_tab(self):
        """Konfiguruje zakładkę wyników"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Wyniki")
        
        # Statystyki
        stats_frame = ttk.LabelFrame(results_frame, text="Statystyki", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, wrap=tk.WORD)
        self.stats_text.pack(fill=tk.X)
        try:
            if THEME == "dark":
                self.stats_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
        except Exception:
            pass
        
        # Lista plików
        files_frame = ttk.LabelFrame(results_frame, text="Sklasyfikowane pliki", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Treeview dla wyników
        self.results_tree = ttk.Treeview(files_frame, 
                                       columns=("artist", "title", "genre", "confidence", "folder"),
                                       show="headings")
        
        self.results_tree.heading("artist", text="Artysta")
        self.results_tree.heading("title", text="Tytuł")
        self.results_tree.heading("genre", text="Gatunek")
        self.results_tree.heading("confidence", text="Pewność")
        self.results_tree.heading("folder", text="Folder")
        
        self.results_tree.column("artist", width=150)
        self.results_tree.column("title", width=200)
        self.results_tree.column("genre", width=120)
        self.results_tree.column("confidence", width=80)
        self.results_tree.column("folder", width=150)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Obsługa podwójnego kliknięcia dla ręcznej klasyfikacji
        self.results_tree.bind("<Double-1>", self.on_file_double_click)
        
        results_scroll = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        results_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_tree.configure(yscrollcommand=results_scroll.set)
        
        # Przyciski eksportu i klasyfikacji
        export_frame = ttk.Frame(results_frame)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(export_frame, text="Eksportuj do CSV", 
                  command=self.export_to_csv).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Zapisz raport", 
                  command=self.save_report).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Importuj z CSV", 
                  command=self.import_from_csv).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(export_frame, text="Ręczna klasyfikacja", 
                  command=self.manual_classify_selected).pack(side=tk.LEFT)
        
    def setup_logs_tab(self):
        """Konfiguruje zakładkę logów"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logi")
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        try:
            if THEME == "dark":
                self.log_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
        except Exception:
            pass
        
        # Przyciski logów
        log_buttons_frame = ttk.Frame(logs_frame)
        log_buttons_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(log_buttons_frame, text="Wyczyść logi", 
                  command=self.clear_logs).pack(side=tk.LEFT)
        ttk.Button(log_buttons_frame, text="Zapisz logi", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=(5, 0))
        
    def setup_styles(self):
        """Konfiguruje style interfejsu"""
        style = ttk.Style()

        # Konfiguracja kolorów dla ciemnego motywu
        if THEME == "dark":
            style.theme_use("clam")
            style.configure("TLabel", background="#2b2b2b", foreground="#ffffff")
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TLabelFrame", background="#2b2b2b", foreground="#ffffff")
            style.configure("TButton", background="#3a3a3a", foreground="#ffffff")
            style.configure("Horizontal.TProgressbar", background="#5c9ded")
            style.configure("Treeview", background="#2b2b2b", foreground="#ffffff", fieldbackground="#2b2b2b")
            style.configure("Treeview.Heading", background="#3a3a3a", foreground="#ffffff")
            style.map("Treeview", background=[("selected", "#3a3a3a")], foreground=[("selected", "#ffffff")])
            style.configure("TNotebook", background="#2b2b2b")
            style.configure("TNotebook.Tab", background="#3a3a3a", foreground="#ffffff")
            style.map("TNotebook.Tab", background=[("selected", "#5c5c5c")])
            style.configure("TCheckbutton", background="#2b2b2b", foreground="#ffffff")
            style.configure("TRadiobutton", background="#2b2b2b", foreground="#ffffff")
            style.configure("TEntry", fieldbackground="#1f1f1f", foreground="#ffffff")
            # Teksty w panelach
            try:
                self.root.configure(bg="#2b2b2b")
            except Exception:
                pass
            # Tk klasyczne widgety: Text / Listbox wymagają ręcznej konfiguracji
            try:
                if hasattr(self, 'stats_text') and isinstance(self.stats_text, tk.Text):
                    self.stats_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
                if hasattr(self, 'log_text'):
                    self.log_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
                # Listbox w dialogu ręcznej klasyfikacji ustawimy przy tworzeniu
            except Exception:
                pass

    def apply_theme(self):
        """Zastosowuje wybrany motyw (light/dark) dynamicznie"""
        chosen = self.theme_var.get()
        style = ttk.Style()
        if chosen == "dark":
            style.theme_use("clam")
            style.configure("TLabel", background="#2b2b2b", foreground="#ffffff")
            style.configure("TFrame", background="#2b2b2b")
            style.configure("TLabelFrame", background="#2b2b2b", foreground="#ffffff")
            style.configure("TButton", background="#3a3a3a", foreground="#ffffff")
            style.configure("Horizontal.TProgressbar", background="#5c9ded")
            try:
                self.root.configure(bg="#2b2b2b")
            except Exception:
                pass
            # Skonfiguruj panel AI dla dark
            # Zostawiamy panel uzasadnień w czerni na białym tle dla czytelności
            try:
                self.ai_panel_frame.configure(style="TLabelFrame")
                if isinstance(self.ai_reason_label, tk.Text):
                    self.ai_reason_label.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")
                else:
                    self.ai_reason_label.configure(bg="#ffffff", fg="#000000")
            except Exception:
                pass
            # Tekstowe widgety
            try:
                if hasattr(self, 'stats_text'):
                    self.stats_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
                if hasattr(self, 'log_text'):
                    self.log_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
            except Exception:
                pass
            self.apply_user_theme(ttk.Style())
        else:
            style.theme_use("default")
            style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabelFrame", background="#f0f0f0", foreground="#000000")
            style.configure("TButton", background="#e0e0e0", foreground="#000000")
            try:
                self.root.configure(bg="#f0f0f0")
            except Exception:
                pass
            try:
                self.ai_panel_frame.configure(style="TLabelFrame")
                if isinstance(self.ai_reason_label, tk.Text):
                    self.ai_reason_label.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")
                else:
                    self.ai_reason_label.configure(bg="#ffffff", fg="#000000")
            except Exception:
                pass
            try:
                if hasattr(self, 'stats_text'):
                    self.stats_text.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")
                if hasattr(self, 'log_text'):
                    self.log_text.configure(bg="#ffffff", fg="#000000", insertbackground="#000000")
            except Exception:
                pass
            self.apply_user_theme(ttk.Style())

    def _load_saved_api_keys(self):
        """Wczytuje klucze API z pliku user_settings.json do zmiennych środowiskowych"""
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            for env_key in ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'LASTFM_API_KEY', 'OPENAI_API_KEY']:
                if data.get(env_key):
                    os.environ[env_key] = data[env_key]
        except Exception:
            pass

    def load_user_settings(self):
        try:
            with open('user_settings.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.spotify_id_var.set(data.get('SPOTIFY_CLIENT_ID', ''))
            self.spotify_secret_var.set(data.get('SPOTIFY_CLIENT_SECRET', ''))
            self.lastfm_key_var.set(data.get('LASTFM_API_KEY', ''))
            self.openai_key_var.set(data.get('OPENAI_API_KEY', ''))
        except Exception:
            pass

    def save_user_settings(self):
        data = {
            'SPOTIFY_CLIENT_ID': self.spotify_id_var.get(),
            'SPOTIFY_CLIENT_SECRET': self.spotify_secret_var.get(),
            'LASTFM_API_KEY': self.lastfm_key_var.get(),
            'OPENAI_API_KEY': self.openai_key_var.get()
        }
        try:
            with open('user_settings.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            # Aktualizuj środowisko i klienta
            self._load_saved_api_keys()
            # Przeładuj WebSearcher z nowym kluczem
            self.web_searcher = WebSearcher()
            messagebox.showinfo("Zapisano", "Ustawienia API zapisane i zastosowane.")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się zapisać: {e}")

    def load_user_theme(self):
        try:
            with open('user_theme.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def save_user_theme(self, theme_dict):
        try:
            with open('user_theme.json', 'w', encoding='utf-8') as f:
                json.dump(theme_dict, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def apply_user_theme(self, style):
        theme = self.load_user_theme()
        if not theme:
            return
        bg = theme.get('background')
        frame_bg = theme.get('frame_bg', bg)
        label_fg = theme.get('label_fg')
        button_bg = theme.get('button_bg')
        button_fg = theme.get('button_fg')
        text_bg = theme.get('text_bg')
        text_fg = theme.get('text_fg')
        tree_bg = theme.get('tree_bg')
        tree_fg = theme.get('tree_fg')
        select_bg = theme.get('select_bg')
        select_fg = theme.get('select_fg')
        entry_bg = theme.get('entry_bg')
        entry_fg = theme.get('entry_fg')
        tab_bg = theme.get('tab_bg', frame_bg)
        tab_fg = theme.get('tab_fg', label_fg)
        try:
            if bg:
                self.root.configure(bg=bg)
                style.configure("TNotebook", background=bg)
            if frame_bg:
                style.configure("TFrame", background=frame_bg)
                style.configure("TLabelFrame", background=frame_bg, foreground=label_fg or '#ffffff')
            if label_fg:
                style.configure("TLabel", foreground=label_fg)
            if button_bg or button_fg:
                style.configure("TButton", background=button_bg or '#3a3a3a', foreground=button_fg or '#ffffff')
            if text_bg or text_fg:
                if hasattr(self, 'stats_text'):
                    self.stats_text.configure(bg=text_bg or '#1f1f1f', fg=text_fg or '#eaeaea', insertbackground=text_fg or '#eaeaea')
                if hasattr(self, 'log_text'):
                    self.log_text.configure(bg=text_bg or '#1f1f1f', fg=text_fg or '#eaeaea', insertbackground=text_fg or '#eaeaea')
            if tree_bg or tree_fg:
                style.configure("Treeview", background=tree_bg or '#2b2b2b', foreground=tree_fg or '#ffffff', fieldbackground=tree_bg or '#2b2b2b')
            if select_bg or select_fg:
                style.map("Treeview", background=[["selected", select_bg or '#3a3a3a']], foreground=[["selected", select_fg or '#ffffff']])
            if tab_bg or tab_fg:
                style.configure("TNotebook.Tab", background=tab_bg or '#3a3a3a', foreground=tab_fg or '#ffffff')
            if entry_bg or entry_fg:
                style.configure("TEntry", fieldbackground=entry_bg or '#1f1f1f', foreground=entry_fg or '#ffffff')
        except Exception:
            pass

    def open_color_options_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Dostrajanie kolorów motywu")
        dialog.geometry("520x480")
        dialog.transient(self.root)
        dialog.grab_set()
        try:
            if self.theme_var.get() == 'dark':
                dialog.configure(bg="#2b2b2b")
        except Exception:
            pass

        fields = [
            ("background", "Tło aplikacji"),
            ("frame_bg", "Tło ramek"),
            ("label_fg", "Tekst etykiet"),
            ("button_bg", "Tło przycisków"),
            ("button_fg", "Tekst przycisków"),
            ("text_bg", "Tło pól tekstowych"),
            ("text_fg", "Tekst pól tekstowych"),
            ("tree_bg", "Tło list/Treeview"),
            ("tree_fg", "Tekst list/Treeview"),
            ("select_bg", "Zaznaczenie tło"),
            ("select_fg", "Zaznaczenie tekst"),
            ("entry_bg", "Tło pól wejściowych"),
            ("entry_fg", "Tekst pól wejściowych"),
            ("tab_bg", "Zakładki tło"),
            ("tab_fg", "Zakładki tekst")
        ]

        current = self.load_user_theme()
        vars_map = {}
        grid = ttk.Frame(dialog)
        grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for i, (key, label) in enumerate(fields):
            ttk.Label(grid, text=label).grid(row=i, column=0, sticky=tk.W, pady=4)
            v = tk.StringVar(value=current.get(key, ''))
            vars_map[key] = v
            ttk.Entry(grid, textvariable=v, width=20).grid(row=i, column=1, sticky=tk.W, padx=(10,0))
            def make_pick(k):
                return lambda: (
                    (lambda c: vars_map[k].set(c[1] or vars_map[k].get()))(colorchooser.askcolor(initialcolor=vars_map[k].get() or '#000000'))
                )
            ttk.Button(grid, text="Wybierz…", command=make_pick(key)).grid(row=i, column=2, padx=(10,0))

        btns = ttk.Frame(dialog)
        btns.pack(fill=tk.X, padx=10, pady=(0,10))
        def apply_and_save():
            theme = {k: v.get() for k, v in vars_map.items() if v.get()}
            self.save_user_theme(theme)
            self.apply_theme()
            dialog.destroy()
        ttk.Button(btns, text="Zastosuj i zapisz", command=apply_and_save).pack(side=tk.RIGHT)
        def cancel():
            dialog.destroy()
        ttk.Button(btns, text="Anuluj", command=cancel).pack(side=tk.RIGHT, padx=(10,0))
    
    def browse_source_dir(self):
        """Otwiera dialog wyboru katalogu źródłowego"""
        directory = filedialog.askdirectory(title="Wybierz katalog z muzyką")
        if directory:
            self.source_dir.set(directory)
    
    def browse_output_dir(self):
        """Otwiera dialog wyboru katalogu docelowego"""
        directory = filedialog.askdirectory(title="Wybierz katalog docelowy")
        if directory:
            self.output_dir.set(directory)
    
    def scan_files(self):
        """Skanuje katalog w poszukiwaniu plików muzycznych"""
        source_path = Path(self.source_dir.get())
        
        if not source_path.exists():
            messagebox.showerror("Błąd", "Katalog źródłowy nie istnieje!")
            return
        
        self.log_message("Rozpoczynam skanowanie plików...")
        self.status_var.set("Skanowanie plików...")
        
        # Uruchomienie w osobnym wątku
        thread = threading.Thread(target=self._scan_files_thread, args=(source_path,))
        thread.daemon = True
        thread.start()
    
    def _scan_files_thread(self, source_path):
        """Wątek skanowania plików"""
        try:
            self.music_files = self.metadata_analyzer.scan_directory(
                source_path, self.recursive_scan.get()
            )
            
            self.root.after(0, self._scan_files_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Błąd podczas skanowania: {e}"))
    
    def _scan_files_complete(self):
        """Callback po zakończeniu skanowania"""
        count = len(self.music_files)
        self.log_message(f"Znaleziono {count} plików muzycznych")
        self.status_var.set(f"Znaleziono {count} plików")
        
        if count == 0:
            messagebox.showwarning("Uwaga", "Nie znaleziono plików muzycznych!")
    
    def analyze_files(self):
        """Analizuje i klasyfikuje pliki"""
        if not self.music_files:
            messagebox.showwarning("Uwaga", "Najpierw zeskanuj pliki!")
            return
        
        self.log_message("Rozpoczynam analizę i klasyfikację...")
        self.status_var.set("Analizowanie plików...")
        self.progress_var.set(0)
        # Wyczyść panel uzasadnień AI (pojedyncza wiadomość)
        try:
            # Reset panelu i bufora uzasadnień przy starcie nowej analizy
            self._set_ai_reason_text("")
            self.ai_reasons_cache = []
            self._current_ai_text = ""
            if self._rotation_job:
                try:
                    self.root.after_cancel(self._rotation_job)
                except Exception:
                    pass
                self._rotation_job = None
        except Exception:
            pass
        
        # Uruchomienie w osobnym wątku
        thread = threading.Thread(target=self._analyze_files_thread)
        thread.daemon = True
        thread.start()
        
        # Uruchomienie monitorowania postępu
        self.root.after(100, self._check_progress)
    
    def _analyze_files_thread(self):
        """Wątek analizy plików"""
        try:
            self.classifications = []
            total_files = len(self.music_files)
            
            for i, file_path in enumerate(self.music_files):
                # Analiza metadanych
                metadata = self.metadata_analyzer.extract_metadata(file_path)
                
                # Uzupełnianie brakujących metadanych przez ChatGPT (jeśli włączone)
                if self.use_web_search.get():
                    metadata = self.web_searcher.enhance_metadata_with_ai(metadata, file_path.name)
                
                # Wyszukiwanie w internecie (jeśli włączone)
                web_info = None
                structure_detected = True
                if self.use_web_search.get():
                    artist = metadata.get('artist', '')
                    title = metadata.get('title', '')
                    
                    if not artist or not title:
                        # Próba wyciągnięcia z nazwy pliku i sprawdzenie struktury
                        filename_info = self.web_searcher.search_by_filename(file_path.name)
                        artist = filename_info.get('artist', artist)
                        title = filename_info.get('title', title)
                        structure_detected = filename_info.get('structure_detected', False)
                    
                    if artist and title:
                        web_info = self.web_searcher.search_track_info(artist, title)
                
                # Jeśli nie wykryto struktury "Artysta - Tytuł", nie klasyfikujemy
                if not structure_detected:
                    classification = {
                        'file_path': str(file_path),
                        'primary_genre': 'unknown',
                        'confidence_score': 0.0,
                        'suggested_folder': 'Unsorted'
                    }
                    # Wyślij uzasadnienie do panelu AI (krótka informacja, bez nazwy pliku)
                    reason_msg = "Brak wykrytej struktury 'Artysta - Tytuł'. Plik przeniesiony do 'Unsorted'."
                    self.progress_queue.put(('ai_reason', reason_msg))
                else:
                    # Klasyfikacja gatunku
                    classification = self.genre_classifier.classify_track(metadata, web_info)
                    # Wydobądź uzasadnienie z AI jeśli dostępne
                    reason_msg = None
                    try:
                        if web_info and isinstance(web_info, dict):
                            ai_analysis = web_info.get('additional_info', {}).get('ai_analysis', {})
                            if ai_analysis.get('reasoning'):
                                reason_msg = ai_analysis.get('reasoning')
                        if not reason_msg and metadata.get('ai_reasoning'):
                            reason_msg = metadata.get('ai_reasoning')
                        # Fallback: krótki opis źródeł punktacji
                        if not reason_msg and classification.get('analysis_details'):
                            breakdown = classification['analysis_details'].get('score_breakdown', {})
                            top_sources = []
                            for genre, data in breakdown.items():
                                sources = data.get('sources', [])
                                if sources:
                                    top_sources.append(f"{genre}: {', '.join(sources[:3])}")
                            if top_sources:
                                reason_msg = "Źródła klasyfikacji -> " + ", ".join(top_sources[:3])
                    except Exception:
                        pass
                    if reason_msg:
                        self.progress_queue.put(('ai_reason', reason_msg))
                
                classification['metadata'] = metadata
                classification['web_info'] = web_info
                
                self.classifications.append(classification)
                
                # Aktualizacja postępu
                progress = ((i + 1) / total_files) * 100
                self.progress_queue.put(('progress', progress))
                self.progress_queue.put(('status', f"Analizowanie {i+1}/{total_files}: {file_path.name}"))
            
            self.progress_queue.put(('complete', None))
            
        except Exception as e:
            self.progress_queue.put(('error', str(e)))
    
    def _check_progress(self):
        """Sprawdza postęp analizy"""
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == 'progress':
                    self.progress_var.set(data)
                elif msg_type == 'status':
                    self.status_var.set(data)
                elif msg_type == 'ai_reason':
                    self._append_ai_reason(str(data))
                elif msg_type == 'complete':
                    self._analysis_complete()
                    return
                elif msg_type == 'error':
                    self._show_error(f"Błąd podczas analizy: {data}")
                    return
                    
        except queue.Empty:
            pass
        
        # Sprawdź ponownie za 100ms
        self.root.after(100, self._check_progress)

    def _append_ai_reason(self, text: str):
        """Dodaje pełne uzasadnienie AI do bufora i uruchamia rotację."""
        try:
            summary = text.strip()
            # Dodaj do bufora (unikaj duplikatów kolejnych)
            if not self.ai_reasons_cache or self.ai_reasons_cache[-1] != summary:
                self.ai_reasons_cache.append(summary)
            # Jeśli nie ma nic na ekranie i mamy przynajmniej 1 wpis – zacznij rotację
            if not self._current_ai_text and len(self.ai_reasons_cache) >= 1:
                self._start_rotation()
        except Exception:
            pass

    def _start_rotation(self):
        """Uruchamia rotację wyświetlania: co 30s losowy opis z bufora, bez wygaszania."""
        try:
            # Bezpiecznie anuluj poprzednie rotacje
            if self._rotation_job:
                self.root.after_cancel(self._rotation_job)
        except Exception:
            pass
        finally:
            self._rotation_job = None

        def show_random_reason():
            if not self.ai_reasons_cache:
                return
            # Wybór losowego uzasadnienia
            import random
            if len(self.ai_reasons_cache) > 1 and self._current_ai_text:
                # wybierz inną niż obecna, jeśli możliwe
                candidates = [t for t in self.ai_reasons_cache if t != self._current_ai_text]
                next_text = random.choice(candidates) if candidates else random.choice(self.ai_reasons_cache)
            else:
                next_text = random.choice(self.ai_reasons_cache)
            # Jeśli ekran pusty – po prostu pokaż
            if not self._current_ai_text:
                self._set_ai_reason_text("")
                self._fade_set_text(next_text)
            else:
                # Podmień tekst natychmiast bez wygaszania
                self.ai_next_reason = next_text
                self._swap_to_next_ai_reason()
            # Zaplanuj następną rotację za 30s
            self._rotation_job = self.root.after(30000, show_random_reason)

        # Pokaż pierwszy opis natychmiast
        show_random_reason()

    # Usunięto skracanie, wyświetlamy pełne uzasadnienia

    def _fade_set_text(self, text: str):
        """Ustawia tekst natychmiast w pełnej widoczności (bez animacji)."""
        # Anuluj ewentualne wcześniejsze animacje (dla bezpieczeństwa)
        try:
            if self._fade_in_job:
                self.root.after_cancel(self._fade_in_job)
        except Exception:
            pass
        finally:
            self._fade_in_job = None
        try:
            if self._fade_out_job:
                self.root.after_cancel(self._fade_out_job)
        except Exception:
            pass
        finally:
            self._fade_out_job = None

        # Ustaw tekst natychmiast
        self._set_ai_reason_text(text)
        # Ustaw wysoką kontrastowość dla ciemnego motywu
        # Kolor tekstu pozostaje czarny dla czytelności
        self._current_ai_text = text

    def _swap_to_next_ai_reason(self):
        """Natychmiast zamienia tekst na kolejny zapisany opis (bez wygaszania)."""
        # Anuluj ewentualne animacje wygaszania (dla bezpieczeństwa)
        try:
            if self._fade_out_job:
                self.root.after_cancel(self._fade_out_job)
        except Exception:
            pass
        finally:
            self._fade_out_job = None

        next_text = getattr(self, 'ai_next_reason', None)
        self.ai_next_reason = None
        if next_text:
            # Ustaw wysoką kontrastowość dla ciemnego motywu
            # Kolor tekstu pozostaje czarny dla czytelności
            self._set_ai_reason_text(next_text)
            self._current_ai_text = next_text
        else:
            self._set_ai_reason_text("")
            self._current_ai_text = ""

    def _set_ai_reason_text(self, text: str):
        """Ustawia zawartość panelu uzasadnień (Text) jako pełny opis, bez skracania."""
        try:
            self.ai_reason_label.configure(state=tk.NORMAL)
            self.ai_reason_label.delete("1.0", tk.END)
            self.ai_reason_label.insert(tk.END, text)
            self.ai_reason_label.configure(state=tk.DISABLED)
        except Exception:
            try:
                # Fallback gdyby widget był innego typu
                self.ai_reason_label.configure(text=text)
            except Exception:
                pass
    
    def _analysis_complete(self):
        """Callback po zakończeniu analizy"""
        count = len(self.classifications)
        self.log_message(f"Zakończono analizę {count} plików")
        self.status_var.set(f"Przeanalizowano {count} plików")
        self.progress_var.set(100)
        
        # Aktualizacja wyników
        self.update_results_display()
        
        # Przełączenie na zakładkę wyników
        self.notebook.select(2)
    
    def sort_files(self):
        """Sortuje pliki do folderów"""
        if not self.classifications:
            messagebox.showwarning("Uwaga", "Najpierw przeanalizuj pliki!")
            return
        
        # Filtrowanie według minimalnego poziomu pewności
        min_conf = self.min_confidence.get()
        filtered_classifications = []
        for c in self.classifications:
            # Pliki w "Unsorted" zawsze powinny być sortowane do tego folderu
            if c.get('suggested_folder') == 'Unsorted':
                filtered_classifications.append(c)
                continue
            # Pozostałe filtrujemy po pewności
            if c.get('confidence_score', 0) >= min_conf:
                filtered_classifications.append(c)
        
        if not filtered_classifications:
            messagebox.showwarning("Uwaga", "Żaden plik nie spełnia kryterium minimalnej pewności!")
            return
        
        # Konfiguracja organizatora plików
        self.file_organizer.output_dir = Path(self.output_dir.get())
        
        self.log_message(f"Rozpoczynam sortowanie {len(filtered_classifications)} plików...")
        self.status_var.set("Sortowanie plików...")
        
        # Uruchomienie w osobnym wątku
        thread = threading.Thread(target=self._sort_files_thread, args=(filtered_classifications,))
        thread.daemon = True
        thread.start()
    
    def _sort_files_thread(self, classifications):
        """Wątek sortowania plików"""
        try:
            report = self.file_organizer.organize_files(classifications, self.dry_run.get(), self.use_pretty_names.get(), self.copy_files.get())
            self.root.after(0, lambda: self._sort_files_complete(report))
            
        except Exception as e:
            self.root.after(0, lambda: self._show_error(f"Błąd podczas sortowania: {e}"))
    
    def _sort_files_complete(self, report):
        """Callback po zakończeniu sortowania"""
        moved = report.get('moved_files', 0)
        copied = report.get('copied_files', 0)
        errors = report.get('errors', 0)

        if self.dry_run.get():
            self.log_message(f"Symulacja zakończona: przeniesień {moved}, kopii {copied}")
            self.status_var.set(f"Symulacja: przeniesień {moved}, kopii {copied}")
        else:
            self.log_message(f"Sortowanie zakończone: przeniesiono {moved}, skopiowano {copied}, błędów {errors}")
            self.status_var.set(f"Przeniesiono {moved}, skopiowano {copied}")
        
        # Wyświetlenie raportu
        self.show_sort_report(report)
    
    def update_results_display(self):
        """Aktualizuje wyświetlanie wyników"""
        # Czyszczenie poprzednich wyników
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Dodawanie nowych wyników
        for classification in self.classifications:
            metadata = classification.get('metadata', {})
            artist = metadata.get('artist', 'Nieznany')
            title = metadata.get('title', metadata.get('filename', 'Nieznany'))
            genre = classification.get('primary_genre', 'unknown')
            confidence = f"{classification.get('confidence_score', 0):.2f}"
            folder = classification.get('suggested_folder', 'Other')
            
            self.results_tree.insert('', 'end', values=(artist, title, genre, confidence, folder))
        
        # Aktualizacja statystyk
        self.update_statistics()
    
    def update_statistics(self):
        """Aktualizuje statystyki"""
        if not self.classifications:
            return
        
        stats = self.genre_classifier.get_genre_statistics(self.classifications)
        
        stats_text = f"""Łączna liczba plików: {stats.get('total_tracks', 0)}
Średni poziom pewności: {stats.get('average_confidence', 0):.2f}
Pliki o wysokiej pewności (>0.7): {stats.get('high_confidence_tracks', 0)}
Pliki o niskiej pewności (<0.3): {stats.get('low_confidence_tracks', 0)}

Rozkład gatunków:
"""
        
        genre_dist = stats.get('genre_distribution', {})
        for genre, count in sorted(genre_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats.get('total_tracks', 1)) * 100
            stats_text += f"  {genre}: {count} ({percentage:.1f}%)\\n"
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
    
    def populate_genres_tree(self):
        """Wypełnia drzewo gatunków"""
        from config import ELECTRONIC_GENRES
        
        for main_genre, subgenres in ELECTRONIC_GENRES.items():
            folder_name = self.genre_classifier._get_folder_name(main_genre)
            parent = self.genres_tree.insert('', 'end', text=main_genre, values=(folder_name,))
            
            for subgenre in subgenres:
                self.genres_tree.insert(parent, 'end', text=f"  {subgenre}", values=("",))
    
    def log_message(self, message):
        """Dodaje wiadomość do logów"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
    
    def clear_logs(self):
        """Czyści logi"""
        self.log_text.delete(1.0, tk.END)
    
    def save_logs(self):
        """Zapisuje logi do pliku"""
        filename = filedialog.asksaveasfilename(
            title="Zapisz logi",
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                messagebox.showinfo("Sukces", "Logi zostały zapisane!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać logów: {e}")
    
    def export_to_csv(self):
        """Eksportuje wyniki do CSV"""
        if not self.classifications:
            messagebox.showwarning("Uwaga", "Brak danych do eksportu!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Eksportuj do CSV",
            defaultextension=".csv",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        
        if filename:
            try:
                import csv
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Plik', 'Artysta', 'Tytuł', 'Gatunek', 'Pewność', 'Folder'])
                    
                    for classification in self.classifications:
                        metadata = classification.get('metadata', {})
                        row = [
                            metadata.get('filename', ''),
                            metadata.get('artist', ''),
                            metadata.get('title', ''),
                            classification.get('primary_genre', ''),
                            classification.get('confidence_score', 0),
                            classification.get('suggested_folder', '')
                        ]
                        writer.writerow(row)
                
                messagebox.showinfo("Sukces", "Dane zostały wyeksportowane!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można wyeksportować danych: {e}")

    def import_from_csv(self):
        """Importuje klasyfikacje z pliku CSV, bez ponownej analizy"""
        filename = filedialog.askopenfilename(
            title="Importuj z CSV",
            filetypes=[("Pliki CSV", "*.csv"), ("Wszystkie pliki", "*.*")]
        )
        if not filename:
            return
        try:
            import csv
            imported = []
            with open(filename, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                # Oczekiwane nagłówki: Plik, Artysta, Tytuł, Gatunek, Pewność, Folder
                for row in reader:
                    file_name = row.get('Plik') or row.get('File') or ''
                    artist = row.get('Artysta') or row.get('Artist') or ''
                    title = row.get('Tytuł') or row.get('Title') or ''
                    genre = row.get('Gatunek') or row.get('Genre') or ''
                    confidence_str = row.get('Pewność') or row.get('Confidence') or '0'
                    folder = row.get('Folder') or ''

                    try:
                        confidence = float(confidence_str)
                    except Exception:
                        confidence = 0.0

                    # Odtwórz pełną ścieżkę pliku jeśli to możliwe
                    # Jeżeli zeskanowaliśmy źródło, spróbuj dopasować po nazwie
                    file_path = ''
                    try:
                        for p in self.music_files:
                            if Path(p).name == file_name:
                                file_path = p
                                break
                    except Exception:
                        pass
                    if not file_path:
                        # Pozwól użyć samej nazwy; FileOrganizer zweryfikuje istnienie
                        file_path = file_name

                    classification = {
                        'file_path': file_path,
                        'primary_genre': genre or 'unknown',
                        'confidence_score': confidence,
                        'suggested_folder': folder or self.genre_classifier._get_folder_name(genre or 'unknown'),
                        'metadata': {
                            'filename': file_name,
                            'artist': artist,
                            'title': title
                        }
                    }
                    imported.append(classification)

            if not imported:
                messagebox.showwarning("Uwaga", "Plik CSV nie zawiera danych do importu")
                return

            self.classifications = imported
            self.update_results_display()
            self.log_message(f"Zaimportowano {len(imported)} rekordów z CSV")
            messagebox.showinfo("Sukces", f"Zaimportowano {len(imported)} rekordów")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie można zaimportować danych: {e}")

    def save_report(self):
        """Zapisuje raport"""
        if not self.classifications:
            messagebox.showwarning("Uwaga", "Brak danych do raportu!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Zapisz raport",
            defaultextension=".txt",
            filetypes=[("Pliki tekstowe", "*.txt"), ("Wszystkie pliki", "*.*")]
        )
        
        if filename:
            try:
                report = self.file_organizer.generate_summary_report(self.classifications)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                messagebox.showinfo("Sukces", "Raport został zapisany!")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać raportu: {e}")
    
    def show_sort_report(self, report):
        """Wyświetla raport sortowania"""
        report_window = tk.Toplevel(self.root)
        report_window.title("Raport sortowania")
        report_window.geometry("600x400")
        
        report_text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        report_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        # Ciemny motyw dla okna raportu
        try:
            if self.theme_var.get() == "dark":
                report_window.configure(bg="#2b2b2b")
                report_text.configure(bg="#1f1f1f", fg="#eaeaea", insertbackground="#eaeaea")
        except Exception:
            pass
        
        # Formatowanie raportu
        report_content = f"""RAPORT SORTOWANIA PLIKÓW
========================

Łączna liczba plików: {report.get('total_files', 0)}
Przetworzone pliki: {report.get('processed_files', 0)}
Przeniesione pliki: {report.get('moved_files', 0)}
Skopiowane pliki: {report.get('copied_files', 0)}
Pominięte pliki: {report.get('skipped_files', 0)}
Błędy: {report.get('errors', 0)}
Tryb testowy: {'Tak' if report.get('dry_run', False) else 'Nie'}

STRUKTURA FOLDERÓW:
"""
        
        folder_structure = report.get('folder_structure', {})
        for folder, info in folder_structure.items():
            file_count = info.get('file_count', 0)
            report_content += f"  {folder}: {file_count} plików\\n"
        
        report_text.insert(1.0, report_content)
        report_text.configure(state='disabled')
    
    def on_file_double_click(self, event):
        """Obsługuje podwójne kliknięcie na plik w drzewie wyników"""
        self.manual_classify_selected()
    
    def manual_classify_selected(self):
        """Otwiera okno ręcznej klasyfikacji dla wybranego pliku"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("Uwaga", "Proszę wybrać plik do klasyfikacji")
            return
        
        item = selection[0]
        file_data = self.results_tree.item(item)
        
        # Pobieranie informacji o pliku
        values = file_data['values']
        if len(values) < 5:
            return
        
        artist, title, current_genre, confidence, folder = values
        
        # Znajdowanie pełnej ścieżki pliku
        file_path = None
        for classification in self.classifications:
            if (classification.get('artist', 'Nieznany') == artist and 
                classification.get('title', 'Nieznany') == title):
                file_path = classification.get('file_path')
                break
        
        if not file_path:
            messagebox.showerror("Błąd", "Nie można znaleźć ścieżki pliku")
            return
        
        # Otwieranie okna klasyfikacji
        self.show_manual_classification_dialog(item, file_path, artist, title, current_genre)
    
    def show_manual_classification_dialog(self, tree_item, file_path, artist, title, current_genre):
        """Pokazuje okno dialogowe do ręcznej klasyfikacji"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ręczna klasyfikacja")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        # Ciemny motyw dla okna dialogowego
        try:
            if self.theme_var.get() == "dark":
                dialog.configure(bg="#2b2b2b")
        except Exception:
            pass
        
        # Informacje o pliku
        info_frame = ttk.LabelFrame(dialog, text="Informacje o pliku", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Artysta: {artist}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Tytuł: {title}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Obecny gatunek: {current_genre}").pack(anchor=tk.W)
        
        # Wybór gatunku
        genre_frame = ttk.LabelFrame(dialog, text="Wybierz gatunek", padding=10)
        genre_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Lista gatunków
        from config import ELECTRONIC_GENRES
        genres = list(ELECTRONIC_GENRES.keys()) + ['unknown', 'other']
        
        genre_var = tk.StringVar(value=current_genre)
        
        # Listbox z gatunkami
        listbox_frame = ttk.Frame(genre_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        genre_listbox = tk.Listbox(listbox_frame, selectmode=tk.SINGLE)
        try:
            if self.theme_var.get() == "dark":
                genre_listbox.configure(bg="#1f1f1f", fg="#eaeaea", selectbackground="#3a3a3a", selectforeground="#ffffff")
        except Exception:
            pass
        for genre in sorted(genres):
            genre_listbox.insert(tk.END, genre)
            if genre == current_genre:
                genre_listbox.selection_set(genre_listbox.size() - 1)
        
        genre_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        listbox_scroll = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=genre_listbox.yview)
        listbox_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        genre_listbox.configure(yscrollcommand=listbox_scroll.set)
        
        # Przyciski
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def save_classification():
            selection = genre_listbox.curselection()
            if not selection:
                messagebox.showwarning("Uwaga", "Proszę wybrać gatunek")
                return
            
            new_genre = genre_listbox.get(selection[0])
            
            # Aktualizacja klasyfikacji
            self.update_file_classification(tree_item, file_path, new_genre)
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Zapisz", command=save_classification).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Anuluj", command=cancel).pack(side=tk.RIGHT)
    
    def update_file_classification(self, tree_item, file_path, new_genre):
        """Aktualizuje klasyfikację pliku"""
        # Aktualizacja w drzewie wyników
        current_values = list(self.results_tree.item(tree_item)['values'])
        current_values[2] = new_genre  # gatunek
        current_values[3] = "1.00"     # pewność (ręczna klasyfikacja)
        
        # Mapowanie gatunku na folder
        from config import get_genre_folder_name
        folder = get_genre_folder_name(new_genre)
        current_values[4] = folder
        
        self.results_tree.item(tree_item, values=current_values)
        
        # Aktualizacja w danych klasyfikacji
        for classification in self.classifications:
            if classification.get('file_path') == file_path:
                classification['primary_genre'] = new_genre
                classification['confidence_score'] = 1.0
                classification['suggested_folder'] = folder
                classification['manual_classification'] = True
                break
        
        # Aktualizacja statystyk
        self.update_statistics()
        
        self.log_message(f"Ręcznie sklasyfikowano: {Path(file_path).name} -> {new_genre}")

    def check_chatgpt_status(self):
        """Sprawdza status ChatGPT i wyświetla ostrzeżenie jeśli jest problem"""
        try:
            # Sprawdź czy ChatGPT jest dostępny
            if not self.web_searcher.openai_client:
                self.log_message("UWAGA: ChatGPT nie jest dostępny - brak klucza API")
                return
            
            # Sprawdź czy ChatGPT został wyłączony z powodu braku środków
            if hasattr(self.web_searcher, '_chatgpt_disabled') and self.web_searcher._chatgpt_disabled:
                self.log_message("UWAGA: ChatGPT został wyłączony z powodu braku środków na koncie OpenAI")
                self.log_message("Aplikacja będzie działać w trybie podstawowym bez analizy AI")
                self.log_message("Aby włączyć ChatGPT, dodaj środki na konto: https://platform.openai.com/account/billing")
                
                # Wyświetl okno ostrzeżenia
                messagebox.showwarning(
                    "ChatGPT niedostępny",
                    "ChatGPT został wyłączony z powodu braku środków na koncie OpenAI.\n\n"
                    "Aplikacja będzie działać w trybie podstawowym bez analizy AI.\n\n"
                    "Aby włączyć ChatGPT:\n"
                    "1. Przejdź do https://platform.openai.com/account/billing\n"
                    "2. Dodaj metodę płatności i doładuj konto\n"
                    "3. Uruchom aplikację ponownie"
                )
        except Exception as e:
            self.log_message(f"Błąd podczas sprawdzania statusu ChatGPT: {e}")

    def _show_error(self, message):
        """Wyświetla błąd"""
        messagebox.showerror("Błąd", message)
        self.status_var.set("Błąd")
        self.log_message(f"BŁĄD: {message}")
    
    def run(self):
        """Uruchamia aplikację"""
        self.log_message("Music Genre Sorter uruchomiony")
        self.root.mainloop()

def main():
    """Główna funkcja aplikacji"""
    app = MusicGenreSorterGUI()
    app.run()

if __name__ == "__main__":
    main()