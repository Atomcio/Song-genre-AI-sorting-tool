"""
Konfiguracja aplikacji Music Genre Sorter
"""

import os
from pathlib import Path

# Ścieżki
PROJECT_ROOT = Path(__file__).parent
DEFAULT_MUSIC_DIR = Path.home() / "Music"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "sorted_music"

# Obsługiwane formaty plików
SUPPORTED_FORMATS = {
    '.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.wma'
}

# Gatunki elektroniczne z podgatunkami
ELECTRONIC_GENRES = {
    # 🌌 Pure Ambient & Space
    'ambient': ['ambient', 'pure ambient', 'classic ambient'],
    'dark_ambient': ['dark ambient', 'black ambient', 'horror ambient'],
    'space_ambient': ['space music', 'space ambient', 'cosmic ambient', 'stellar ambient'],
    'isolationism': ['isolationism', 'minimalist ambient', 'cold ambient'],
    'drone_ambient': ['drone ambient', 'drone', 'hypnotic ambient', 'continuous ambient'],
    
    # 🏰 Atmospheric / Fantasy Ambient
    'dungeon_synth': ['dungeon synth', 'fantasy ambient', 'medieval ambient'],
    'ethereal_ambient': ['ethereal ambient', 'ethereal', 'angelic ambient'],
    'neoclassical_ambient': ['neoclassical ambient', 'orchestral ambient', 'symphonic ambient'],
    'new_age_ambient': ['new age', 'healing ambient', 'meditation music', 'wellness ambient'],
    
    # 🌊 Dub & Psy Ambient
    'ambient_dub': ['ambient dub', 'dub ambient', 'spacious dub'],
    'psydub': ['psydub', 'psychedelic dub', 'trippy dub'],
    'dub_techno': ['dub techno', 'ambient techno', 'minimal dub'],
    'chill_dub': ['chill dub', 'downtempo dub', 'relaxed dub'],
    
    # 🌒 Industrial Ambient / Darker Side
    'ambient_industrial': ['ambient industrial', 'industrial ambient', 'dark industrial'],
    'death_industrial': ['death industrial', 'harsh ambient', 'extreme industrial'],
    'power_noise': ['power noise', 'rhythmic noise', 'harsh noise'],
    'illbient': ['illbient', 'ambient hip hop', 'industrial downtempo'],
    
    # 🌀 Dream & Hypnagogic
    'dreampunk': ['dreampunk', 'dream ambient', 'surreal ambient'],
    'dream_ambient': ['dream ambient', 'oneiric ambient', 'sleep ambient'],
    'hypnagogic_pop': ['hypnagogic pop', 'chillwave', 'lo-fi ambient'],
    'vaporwave_ambient': ['vaporwave ambient', 'mallsoft', 'retro ambient'],
    
    # 🎛️ Experimental Ambient
    'electroacoustic_ambient': ['electroacoustic ambient', 'acousmatic', 'concrete ambient'],
    'soundscape': ['soundscape', 'field recording', 'environmental ambient'],
    'microsound': ['microsound', 'micro ambient', 'granular ambient'],
    'lowercase': ['lowercase', 'ultra quiet', 'minimal sound'],
    'onkyokei': ['onkyokei', 'japanese minimal', 'extreme reduction'],
    
    # 🕯 Ritual / Mystical Ambient
    'ritual_ambient': ['ritual ambient', 'ceremonial ambient', 'mystical ambient'],
    'martial_ambient': ['martial ambient', 'military ambient', 'war ambient'],
    'shamanic_ambient': ['shamanic ambient', 'tribal ambient', 'spiritual ambient'],
    
    # 🎷 Fusion Ambient
    'jazz_ambient': ['jazz ambient', 'nu-jazztronica', 'ambient jazz'],
    'post_rock_ambient': ['post-rock ambient', 'ambient guitars', 'cinematic ambient'],
    'folk_ambient': ['folk ambient', 'folktronica', 'organic ambient'],
    'electroacoustic_improv': ['electroacoustic improvisation', 'free ambient', 'improv ambient'],
    
    # Techno Family
    'techno': ['techno', 'minimal techno', 'detroit techno', 'berlin techno', 'acid techno'],
    'industrial_techno': ['industrial techno', 'hard techno', 'industrial', 'ebm', 'power electronics'],
    'dub_techno': ['dub techno', 'minimal dub', 'deep techno', 'atmospheric techno'],
    'acid_techno': ['acid techno', 'acid', '303', 'tb-303', 'acid house'],
    
    # House Variants
    'house': ['house', 'classic house', 'chicago house', 'vocal house'],
    'deep_house': ['deep house', 'soulful house', 'jazzy house', 'organic house'],
    'tech_house': ['tech house', 'minimal house', 'groove house'],
    'progressive_house': ['progressive house', 'prog house', 'melodic house'],
    'tribal_house': ['tribal house', 'afro house', 'ethnic house', 'percussion house'],
    
    # Trance & Progressive
    'trance': ['trance', 'classic trance', 'vocal trance', 'uplifting trance'],
    'progressive_trance': ['progressive trance', 'prog trance', 'melodic trance'],
    'psytrance': ['psytrance', 'psychedelic trance', 'goa trance', 'full-on', 'dark psy'],
    'hard_trance': ['hard trance', 'acid trance', 'schranz'],
    
    # Breakbeat & Drum'n'Bass
    'drum_and_bass': ['drum and bass', 'dnb', 'jungle', 'liquid dnb', 'neurofunk'],
    'breakbeat': ['breakbeat', 'big beat', 'nu skool breaks', 'funky breaks'],
    'breakcore': ['breakcore', 'digital hardcore', 'speedcore', 'mashcore'],
    
    # Experimental & IDM
    'experimental': ['experimental', 'idm', 'glitch', 'avant-garde', 'noise', 'microsound'],
    'glitch': ['glitch', 'glitch hop', 'microhouse', 'clicks and cuts'],
    'idm': ['idm', 'intelligent dance music', 'braindance', 'electronica'],
    
    # Downtempo & Chill
    'downtempo': ['downtempo', 'chillout', 'trip hop', 'lounge', 'nu jazz'],
    'trip_hop': ['trip hop', 'abstract hip hop', 'instrumental hip hop'],
    'chillstep': ['chillstep', 'melodic dubstep', 'future garage', 'liquid dubstep'],
    
    # Bass Music (bez dubstep)
    'future_bass': ['future bass', 'melodic bass', 'chill bass', 'wave'],
    'trap': ['trap', 'future trap', 'hybrid trap', 'festival trap'],
    'uk_garage': ['uk garage', '2-step', 'speed garage', 'bassline'],
    'bass_music': ['bass music', 'heavy bass', 'sub bass', 'bass heavy'],
    
    # Hardcore & Hard Dance
    'hardcore': ['hardcore', 'gabber', 'happy hardcore', 'frenchcore'],
    'hardstyle': ['hardstyle', 'euphoric hardstyle', 'rawstyle', 'hardcore'],
    'speedcore': ['speedcore', 'terrorcore', 'extratone', 'splittercore'],
    
    # Retro & Synthwave
    'synthwave': ['synthwave', 'retrowave', 'outrun', 'darksynth', 'cyberpunk'],
    'vaporwave': ['vaporwave', 'mallsoft', 'future funk', 'slushwave'],
    'new_wave': ['new wave', 'synthpop', 'darkwave', 'coldwave'],
    
    # Minimal & Microhouse
    'minimal': ['minimal', 'microhouse', 'minimal house', 'minimal techno'],
    'microhouse': ['microhouse', 'minimal house', 'clicks and cuts house'],
    
    # Electro & Breaks
    'electro': ['electro', 'electro funk', 'miami bass', 'freestyle'],
    'electroclash': ['electroclash', 'new rave', 'fidget house'],
    
    # Specialty & Fusion
    'psydub': ['psydub', 'dub', 'psychedelic dub', 'bass music'],
    'world_electronic': ['world electronic', 'ethnic electronic', 'tribal electronic'],
    'cinematic': ['cinematic', 'soundtrack', 'film score', 'epic electronic']
}

# Słowa kluczowe dla klasyfikacji
GENRE_KEYWORDS = {
    # 🌌 Pure Ambient & Space
    'ambient': ['ambient', 'pure', 'classic', 'atmospheric', 'meditation', 'relaxing', 'calm'],
    'dark_ambient': ['dark', 'black', 'horror', 'sinister', 'ominous', 'scary', 'haunting'],
    'space_ambient': ['space', 'cosmic', 'stellar', 'galaxy', 'universe', 'celestial', 'astral'],
    'isolationism': ['isolationism', 'minimal', 'cold', 'distant', 'sparse', 'empty'],
    'drone_ambient': ['drone', 'continuous', 'hypnotic', 'sustained', 'monotone', 'meditative'],
    
    # 🏰 Atmospheric / Fantasy Ambient
    'dungeon_synth': ['dungeon', 'fantasy', 'medieval', 'castle', 'knight', 'sword', 'magic'],
    'ethereal_ambient': ['ethereal', 'angelic', 'heavenly', 'divine', 'spiritual', 'transcendent'],
    'neoclassical_ambient': ['neoclassical', 'orchestral', 'symphonic', 'classical', 'strings'],
    'new_age_ambient': ['new age', 'healing', 'wellness', 'therapy', 'chakra', 'meditation'],
    
    # 🌊 Dub & Psy Ambient
    'ambient_dub': ['dub', 'echo', 'reverb', 'spacious', 'deep', 'atmospheric'],
    'psydub': ['psychedelic', 'trippy', 'dub', 'bass', 'deep', 'mind-bending'],
    'dub_techno': ['dub', 'techno', 'minimal', 'deep', 'atmospheric', 'echo'],
    'chill_dub': ['chill', 'dub', 'downtempo', 'relaxed', 'laid-back'],
    
    # 🌒 Industrial Ambient / Darker Side
    'ambient_industrial': ['industrial', 'mechanical', 'harsh', 'metallic', 'factory'],
    'death_industrial': ['death', 'extreme', 'harsh', 'brutal', 'aggressive'],
    'power_noise': ['noise', 'rhythmic', 'harsh', 'distorted', 'aggressive'],
    'illbient': ['illbient', 'hip hop', 'urban', 'street', 'downtempo'],
    
    # 🌀 Dream & Hypnagogic
    'dreampunk': ['dream', 'surreal', 'fantasy', 'ethereal', 'otherworldly'],
    'dream_ambient': ['dream', 'sleep', 'oneiric', 'subconscious', 'peaceful'],
    'hypnagogic_pop': ['hypnagogic', 'chillwave', 'lo-fi', 'nostalgic', 'dreamy'],
    'vaporwave_ambient': ['vaporwave', 'mallsoft', 'retro', '80s', 'nostalgic'],
    
    # 🎛️ Experimental Ambient
    'electroacoustic_ambient': ['electroacoustic', 'acousmatic', 'concrete', 'experimental'],
    'soundscape': ['soundscape', 'field recording', 'environmental', 'natural'],
    'microsound': ['microsound', 'granular', 'micro', 'detailed', 'precise'],
    'lowercase': ['lowercase', 'quiet', 'minimal', 'subtle', 'whisper'],
    'onkyokei': ['onkyokei', 'japanese', 'minimal', 'reduction', 'silence'],
    
    # 🕯 Ritual / Mystical Ambient
    'ritual_ambient': ['ritual', 'ceremonial', 'mystical', 'sacred', 'spiritual'],
    'martial_ambient': ['martial', 'military', 'war', 'battle', 'heroic'],
    'shamanic_ambient': ['shamanic', 'tribal', 'spiritual', 'indigenous', 'ancient'],
    
    # 🎷 Fusion Ambient
    'jazz_ambient': ['jazz', 'nu-jazz', 'smooth', 'improvisation', 'saxophone'],
    'post_rock_ambient': ['post-rock', 'guitar', 'cinematic', 'emotional', 'epic'],
    'folk_ambient': ['folk', 'acoustic', 'organic', 'natural', 'traditional'],
    'electroacoustic_improv': ['improvisation', 'free', 'experimental', 'spontaneous'],
    
    # Techno Family
    'techno': ['techno', 'electronic', 'dance', 'club', 'rave', 'underground', 'driving'],
    'industrial_techno': ['industrial', 'harsh', 'aggressive', 'mechanical', 'distorted', 'hard'],
    'dub_techno': ['dub', 'minimal', 'deep', 'atmospheric', 'echo', 'spacious'],
    'acid_techno': ['acid', '303', 'squelch', 'distorted', 'psychedelic'],
    
    # House Variants
    'house': ['house', 'groove', 'funky', 'rhythmic', 'bass', 'four-on-floor'],
    'deep_house': ['deep', 'soulful', 'jazzy', 'organic', 'warm', 'smooth'],
    'tech_house': ['tech', 'minimal', 'groove', 'driving', 'percussive'],
    'progressive_house': ['progressive', 'melodic', 'uplifting', 'emotional', 'journey'],
    'tribal_house': ['tribal', 'ethnic', 'percussion', 'drums', 'ritual', 'african'],
    
    # Trance & Progressive
    'trance': ['trance', 'uplifting', 'euphoric', 'emotional', 'melodic', 'epic'],
    'progressive_trance': ['progressive', 'journey', 'evolving', 'atmospheric', 'deep'],
    'psytrance': ['psychedelic', 'trippy', 'forest', 'goa', 'full-on', 'dark'],
    'hard_trance': ['hard', 'schranz', 'aggressive', 'driving', 'intense'],
    
    # Breakbeat & Drum'n'Bass
    'drum_and_bass': ['dnb', 'jungle', 'liquid', 'neurofunk', 'amen', 'breakbeat'],
    'breakbeat': ['breaks', 'funky', 'big beat', 'chopped', 'sampled'],
    'breakcore': ['breakcore', 'hardcore', 'chaotic', 'aggressive', 'digital'],
    
    # Experimental & IDM
    'experimental': ['experimental', 'abstract', 'avant', 'weird', 'unusual', 'innovative'],
    'glitch': ['glitch', 'clicks', 'cuts', 'digital', 'fragmented', 'stuttering'],
    'idm': ['intelligent', 'braindance', 'complex', 'cerebral', 'intricate'],
    
    # Downtempo & Chill
    'downtempo': ['downtempo', 'chill', 'relaxed', 'slow', 'mellow', 'laid-back'],
    'trip_hop': ['trip hop', 'abstract', 'hip hop', 'cinematic', 'moody'],
    'chillstep': ['chill', 'melodic', 'emotional', 'dubstep', 'liquid'],
    
    # Bass Music (bez dubstep)
    'future_bass': ['future', 'melodic', 'emotional', 'uplifting', 'colorful'],
    'trap': ['trap', 'hip hop', 'festival', 'heavy', 'aggressive'],
    'uk_garage': ['garage', '2-step', 'shuffled', 'syncopated', 'uk'],
    'bass_music': ['bass', 'heavy bass', 'sub bass', 'low end', 'deep bass'],
    
    # Hardcore & Hard Dance
    'hardcore': ['hardcore', 'gabber', 'aggressive', 'fast', 'intense'],
    'hardstyle': ['hardstyle', 'euphoric', 'raw', 'kick', 'reverse bass'],
    'speedcore': ['speedcore', 'terror', 'extreme', 'fast', 'chaotic'],
    
    # Retro & Synthwave
    'synthwave': ['synthwave', 'retro', '80s', 'neon', 'cyberpunk', 'nostalgic'],
    'vaporwave': ['vaporwave', 'aesthetic', 'nostalgic', 'dreamy', 'slowed'],
    'new_wave': ['new wave', 'synthpop', 'dark', 'cold', 'minimal'],
    
    # Minimal & Microhouse
    'minimal': ['minimal', 'repetitive', 'subtle', 'hypnotic', 'stripped'],
    'microhouse': ['micro', 'clicks', 'minimal', 'detailed', 'precise'],
    
    # Electro & Breaks
    'electro': ['electro', 'funk', 'robot', 'vocoder', 'miami'],
    'electroclash': ['electroclash', 'new rave', 'fidget', 'aggressive'],
    
    # Specialty & Fusion
    'psydub': ['psychedelic', 'dub', 'bass', 'trippy', 'deep'],
    'world_electronic': ['world', 'ethnic', 'traditional', 'fusion', 'cultural'],
    'cinematic': ['cinematic', 'soundtrack', 'epic', 'emotional', 'orchestral']
}

# Konfiguracja API
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')
LASTFM_API_KEY = os.getenv('LASTFM_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Ustawienia analizy
MIN_CONFIDENCE_SCORE = 0.6  # Minimalny poziom pewności klasyfikacji
MAX_SEARCH_RESULTS = 5      # Maksymalna liczba wyników wyszukiwania
ANALYSIS_TIMEOUT = 30       # Timeout dla analizy pojedynczego pliku (sekundy)

# Ustawienia GUI
WINDOW_SIZE = "1200x800"
THEME = "dark"  # "light" lub "dark"

# Mapowanie BPM do gatunków
BPM_GENRE_MAPPING = {
    (50, 70): ['ambient', 'dub_ambient', 'psybient', 'cinematic'],
    (70, 90): ['downtempo', 'trip_hop', 'chillstep', 'vaporwave'],
    (90, 110): ['deep_house', 'dub', 'uk_garage', 'future_garage'],
    (110, 125): ['house', 'tech_house', 'progressive_house', 'tribal_house'],
    (125, 135): ['techno', 'minimal_techno', 'dub_techno', 'acid_techno'],
    (135, 145): ['trance', 'progressive_trance', 'psytrance', 'hard_trance'],
    (145, 160): ['drum_and_bass', 'breakbeat', 'jungle', 'neurofunk'],
    (160, 180): ['hardcore', 'hardstyle', 'gabber', 'happy_hardcore'],
    (180, 220): ['speedcore', 'breakcore', 'extratone'],
    (70, 140): ['dubstep', 'future_bass', 'trap', 'bass_music'],
    (80, 120): ['synthwave', 'new_wave', 'electroclash'],
    (120, 140): ['electro', 'electro_house', 'big_room'],
    (100, 130): ['glitch', 'idm', 'experimental_electronic']
}

# Ustawienia klasyfikacji
CLASSIFICATION_SETTINGS = {
    'min_confidence_threshold': 0.3,
    'high_confidence_threshold': 0.7,
    'use_filename_analysis': True,
    'use_web_search': True,
    'use_audio_features': True,
    'weight_metadata': 0.4,
    'weight_web_info': 0.3,
    'weight_audio_features': 0.2,
    'weight_filename': 0.1
}

# Ustawienia organizacji plików
FILE_ORGANIZATION_SETTINGS = {
    'create_playlists': True,
    'backup_original_structure': True,
    'handle_duplicates': 'rename',  # 'rename', 'skip', 'overwrite'
    'needs_review_folder': 'Needs Review',
    'unknown_genre_folder': 'Other',
    'min_files_for_subfolder': 50
}

# Mapowanie folderów
FOLDER_MAPPING = {
    # Pure Ambient & Space
    'ambient': 'Ambient',
    'dark_ambient': 'Dark Ambient',
    'space_ambient': 'Space Music',
    'isolationism': 'Isolationism',
    'drone_ambient': 'Drone',
    
    # Atmospheric / Fantasy
    'dungeon_synth': 'Dungeon Synth',
    'ethereal_ambient': 'Ethereal',
    'neoclassical_ambient': 'Neoclassical',
    'new_age_ambient': 'New Age',
    
    # Dub & Psy
    'ambient_dub': 'Ambient Dub',
    'psydub': 'Psydub',
    'dub_techno': 'Dub Techno',
    'chill_dub': 'Chill Dub',
    
    # Industrial & Dark
    'ambient_industrial': 'Ambient Industrial',
    'death_industrial': 'Death Industrial',
    'power_noise': 'Power Noise',
    'illbient': 'Illbient',
    
    # Dream & Hypnagogic
    'dreampunk': 'Dreampunk',
    'dream_ambient': 'Dream Ambient',
    'hypnagogic_pop': 'Hypnagogic',
    'vaporwave_ambient': 'Vaporwave',
    
    # Experimental
    'electroacoustic_ambient': 'Electroacoustic',
    'soundscape': 'Soundscape',
    'microsound': 'Microsound',
    'lowercase': 'Lowercase',
    'onkyokei': 'Onkyokei',
    
    # Ritual & Mystical
    'ritual_ambient': 'Ritual',
    'martial_ambient': 'Martial',
    'shamanic_ambient': 'Shamanic',
    
    # Fusion
    'jazz_ambient': 'Jazz Ambient',
    'post_rock_ambient': 'Post Rock Ambient',
    'folk_ambient': 'Folk Ambient',
    'electroacoustic_improv': 'Electroacoustic Improv',
    
    # Pozostale ambient
    'field_recording': 'Field Recording',
    'meditation': 'Meditation',
    'nature_sounds': 'Nature Sounds',
    'chillstep': 'Chillstep',
    
    # Techno
    'techno': 'Techno',
    'industrial_techno': 'Industrial Techno',
    'acid_techno': 'Acid Techno',
    
    # House
    'house': 'House',
    'deep_house': 'Deep House',
    'tech_house': 'Tech House',
    'progressive_house': 'Progressive House',
    'tribal_house': 'Tribal House',
    
    # Trance
    'trance': 'Trance',
    'progressive_trance': 'Progressive Trance',
    'psytrance': 'Psytrance',
    'hard_trance': 'Hard Trance',
    
    # Drum & Bass
    'drum_and_bass': 'Drum And Bass',
    'breakbeat': 'Breakbeat',
    'breakcore': 'Breakcore',
    
    # Experimental
    'experimental': 'Experimental',
    'glitch': 'Glitch',
    'idm': 'IDM',
    
    # Downtempo
    'downtempo': 'Downtempo',
    'trip_hop': 'Trip Hop',
    'chillstep': 'Chillstep',
    
    # Bass Music
    'future_bass': 'Future Bass',
    'trap': 'Trap',
    'uk_garage': 'UK Garage',
    'bass_music': 'Bass Music',
    
    # Hardcore
    'hardcore': 'Hardcore',
    'hardstyle': 'Hardstyle',
    'speedcore': 'Speedcore',
    
    # Synthwave
    'synthwave': 'Synthwave',
    'vaporwave': 'Vaporwave',
    'new_wave': 'New Wave',
    
    # Minimal
    'minimal': 'Minimal',
    'microhouse': 'Microhouse',
    
    # Electro
    'electro': 'Electro',
    'electroclash': 'Electroclash',
    
    # Other
    'world_electronic': 'World Electronic',
    'cinematic': 'Cinematic'
}

# Ustawienia cache
CACHE_SETTINGS = {
    'cache_dir': Path.home() / '.music_sorter_cache',
    'enable_metadata_cache': True,
    'enable_web_cache': True,
    'cache_expiry_days': 30
}

# Ustawienia wydajności
PERFORMANCE_SETTINGS = {
    'max_concurrent_web_requests': 5,
    'web_request_delay': 0.1,  # sekundy
    'batch_size': 100,
    'cache_web_results': True,
    'cache_duration': 24 * 60 * 60  # 24 godziny w sekundach
}

# Ustawienia logowania
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_genre_folder_name(genre):
    """Zwraca nazwę folderu dla danego gatunku"""
    return FOLDER_MAPPING.get(genre.lower(), genre.title())

def is_supported_format(file_path):
    """Sprawdza czy format pliku jest obsługiwany"""
    return file_path.suffix.lower() in SUPPORTED_FORMATS

def get_bpm_genres(bpm):
    """Zwraca gatunki pasujące do danego BPM"""
    if not bpm:
        return []
    
    for (min_bpm, max_bpm), genres in BPM_GENRE_MAPPING.items():
        if min_bpm <= bpm < max_bpm:
            return genres
    
    return []

def get_genre_keywords(genre):
    """Zwraca słowa kluczowe dla danego gatunku"""
    return GENRE_KEYWORDS.get(genre.lower(), [])

def create_cache_dir():
    """Tworzy katalog cache jeśli nie istnieje"""
    cache_dir = CACHE_SETTINGS['cache_dir']
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir