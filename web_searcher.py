"""
Moduł do wyszukiwania informacji o utworach w internecie
"""

import requests
import json
import logging
from typing import Dict, List, Optional
from urllib.parse import quote
import time
import re
import openai
import os

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, OPENAI_API_KEY, LASTFM_API_KEY, MAX_SEARCH_RESULTS

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearcher:
    """Klasa do wyszukiwania informacji o utworach w internecie"""
    
    def __init__(self):
        self.spotify_token = None
        self.spotify_token_expires = 0
        # Czytaj klucze z ENV aby możliwe były zmiany w trakcie działania
        self.lastfm_api_key = os.getenv('LASTFM_API_KEY', LASTFM_API_KEY)

        # Inicjalizacja OpenAI z klucza środowiskowego lub configowego
        api_key = os.getenv('OPENAI_API_KEY', OPENAI_API_KEY)
        self.openai_api_key = api_key
        if api_key:
            openai.api_key = api_key
            try:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI API zainicjalizowane")
            except Exception as e:
                logger.warning(f"Nie udało się zainicjalizować OpenAI: {e}")
                self.openai_client = None
        else:
            self.openai_client = None
            logger.warning("Brak klucza OpenAI API - funkcje ChatGPT będą wyłączone")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Music Genre Sorter/1.0'
        })
    
    def search_track_info(self, artist: str, title: str, album: str = "", filename: str = "") -> Dict:
        """
        Wyszukuje informacje o utworze używając różnych źródeł
        
        Args:
            artist: Nazwa artysty
            title: Tytuł utworu
            album: Nazwa albumu (opcjonalne)
            filename: Nazwa pliku (opcjonalne)
            
        Returns:
            Słownik z informacjami o utworze
        """
        results = {
            'artist': artist,
            'title': title,
            'album': album,
            'primary_genre': 'unknown',
            'secondary_genre': None,
            'confidence': 0.0,
            'genres': [],
            'tags': [],
            'year': '',
            'label': '',
            'bpm': '',
            'key': '',
            'energy': '',
            'danceability': '',
            'sources': [],
            'additional_info': {}
        }
        
        try:
            # Wyszukiwanie w Spotify
            if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
                spotify_info = self._search_spotify(artist, title, album)
                if spotify_info:
                    results.update(spotify_info)
                    results['sources'].append('Spotify')
                    results['additional_info']['spotify'] = spotify_info
                    if spotify_info.get('genres'):
                        results['primary_genre'] = spotify_info['genres'][0]
                        results['confidence'] = 0.8
            
            # Wyszukiwanie w Last.fm
            if self.lastfm_api_key:
                lastfm_info = self._search_lastfm(artist, title)
                if lastfm_info:
                    # Łączenie informacji z Last.fm
                    if lastfm_info.get('genres'):
                        results['genres'].extend(lastfm_info['genres'])
                    if lastfm_info.get('tags'):
                        results['tags'].extend(lastfm_info['tags'])
                        if results['primary_genre'] == 'unknown':
                            results['primary_genre'] = lastfm_info['tags'][0]
                            results['confidence'] = 0.6
                    if not results['year'] and lastfm_info.get('year'):
                        results['year'] = lastfm_info['year']
                    results['sources'].append('Last.fm')
                    results['additional_info']['lastfm'] = lastfm_info
            
            # Wyszukiwanie ogólne w internecie
            web_info = self._search_web(artist, title)
            if web_info:
                if web_info.get('genres'):
                    results['genres'].extend(web_info['genres'])
                    if results['primary_genre'] == 'unknown':
                        results['primary_genre'] = web_info['genres'][0]
                        results['confidence'] = 0.4
                if web_info.get('tags'):
                    results['tags'].extend(web_info['tags'])
                results['sources'].append('Web Search')
                results['additional_info']['web'] = web_info
            
            # AI-powered analysis dla trudnych przypadków
            if results['confidence'] < 0.5:
                ai_info = self._ai_powered_analysis(artist, title, filename)
                if ai_info:
                    results['additional_info']['ai_analysis'] = ai_info
                    # Jeśli AI podało BPM, zachowaj go jako web BPM
                    if isinstance(ai_info.get('bpm'), (int, float)):
                        results['bpm'] = str(int(ai_info['bpm']))
                    # Flaga remiksu i styl
                    if ai_info.get('is_remix'):
                        results['tags'].append('remix')
                        if ai_info.get('remix_style'):
                            results['genres'].append(str(ai_info['remix_style']).lower().replace(' ', '_'))
                    if ai_info.get('primary_genre') and ai_info['confidence'] > results['confidence']:
                        results['primary_genre'] = ai_info['primary_genre']
                        results['secondary_genre'] = ai_info.get('secondary_genre')
                        results['confidence'] = ai_info['confidence']
                        results['tags'].extend(ai_info.get('tags', []))
                    results['sources'].append('AI Analysis')
            
            # Analiza nazwy pliku jako ostatnia deska ratunku
            if results['primary_genre'] == 'unknown' and filename:
                filename_info = self.search_by_filename(filename)
                if filename_info.get('primary_genre') != 'unknown':
                    results.update(filename_info)
            
            # Usunięcie duplikatów z gatunków i tagów
            results['genres'] = list(set(results['genres']))
            results['tags'] = list(set(results['tags']))
            
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania informacji o utworze: {e}")
        
        return results
    
    def _get_spotify_token(self) -> Optional[str]:
        """Pobiera token dostępu do Spotify API"""
        if self.spotify_token and time.time() < self.spotify_token_expires:
            return self.spotify_token
            
        try:
            auth_url = 'https://accounts.spotify.com/api/token'
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': SPOTIFY_CLIENT_ID,
                'client_secret': SPOTIFY_CLIENT_SECRET
            }
            
            response = self.session.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.spotify_token = token_data['access_token']
            self.spotify_token_expires = time.time() + token_data['expires_in'] - 60
            
            return self.spotify_token
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania tokenu Spotify: {e}")
            return None
    
    def enhance_metadata_with_ai(self, metadata: Dict, filename: str = "") -> Dict:
        """
        Uzupełnia brakujące metadane używając ChatGPT
        
        Args:
            metadata: Słownik z obecnymi metadanymi
            filename: Nazwa pliku (opcjonalne)
            
        Returns:
            Słownik z uzupełnionymi metadanymi
        """
        try:
            if not self.openai_client:
                logger.warning("OpenAI API niedostępne - pomijam uzupełnianie metadanych")
                return metadata
            
            # Sprawdzenie czy są brakujące metadane
            artist = metadata.get('artist', '').strip()
            title = metadata.get('title', '').strip()
            year = metadata.get('year', '').strip()
            album = metadata.get('album', '').strip()
            
            missing_fields = []
            if not artist:
                missing_fields.append('artist')
            if not title:
                missing_fields.append('title')
            if not year:
                missing_fields.append('year')
            if not album:
                missing_fields.append('album')
            
            if not missing_fields:
                logger.info("Wszystkie metadane są kompletne - pomijam uzupełnianie")
                return metadata
            
            # Przygotowanie promptu dla ChatGPT
            prompt = f"""
Przeanalizuj następujący plik muzyczny i uzupełnij brakujące metadane:

Obecne metadane:
- Artysta: {artist if artist else 'BRAK'}
- Tytuł: {title if title else 'BRAK'}
- Rok: {year if year else 'BRAK'}
- Album: {album if album else 'BRAK'}
- Nazwa pliku: {filename if filename else 'brak'}

Brakujące pola do uzupełnienia: {', '.join(missing_fields)}

Na podstawie dostępnych informacji (nazwa pliku, istniejące metadane) spróbuj określić:
1. Nazwę artysty (jeśli brak)
2. Tytuł utworu (jeśli brak)
3. Rok wydania (jeśli brak)
4. Nazwę albumu (jeśli brak)

Skup się na:
- Analizie nazwy pliku pod kątem wzorców "Artysta - Tytuł", "Artysta - Album - Tytuł", itp.
- Rozpoznawaniu znanych artystów i ich utworów
- Logicznym dopasowaniu na podstawie kontekstu
- Jeśli nie jesteś pewien, lepiej zostaw pole puste niż podać błędną informację

Odpowiedz w formacie JSON:
{{
    "artist": "nazwa_artysty_lub_null",
    "title": "tytuł_utworu_lub_null", 
    "year": "rok_lub_null",
    "album": "nazwa_albumu_lub_null",
    "confidence": 0.85,
    "reasoning": "krótkie uzasadnienie"
}}
"""

            # Zapytanie do ChatGPT
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Jesteś ekspertem od metadanych muzycznych. Analizujesz pliki muzyczne i uzupełniasz brakujące informacje. Odpowiadaj zawsze w formacie JSON. Jeśli nie jesteś pewien jakiejś informacji, lepiej zostaw pole puste (null) niż podać błędną wartość."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=400,
                temperature=0.2
            )
            
            # Parsowanie odpowiedzi
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Odpowiedź ChatGPT dla uzupełnienia metadanych '{filename}': {ai_response}")
            
            # Próba parsowania JSON
            try:
                # Usunięcie ewentualnych znaczników markdown
                if ai_response.startswith('```json'):
                    ai_response = ai_response[7:]
                if ai_response.endswith('```'):
                    ai_response = ai_response[:-3]
                
                result = json.loads(ai_response.strip())
                
                # Walidacja wyników
                if not isinstance(result, dict):
                    raise ValueError("Odpowiedź nie jest słownikiem")
                
                # Uzupełnienie metadanych tylko jeśli ChatGPT podał wartości
                enhanced_metadata = metadata.copy()
                
                if not artist and result.get('artist') and result['artist'] not in ['null', 'None', '']:
                    enhanced_metadata['artist'] = result['artist']
                    logger.info(f"Uzupełniono artystę: {result['artist']}")
                
                if not title and result.get('title') and result['title'] not in ['null', 'None', '']:
                    enhanced_metadata['title'] = result['title']
                    logger.info(f"Uzupełniono tytuł: {result['title']}")
                
                if not year and result.get('year') and result['year'] not in ['null', 'None', '']:
                    enhanced_metadata['year'] = str(result['year'])
                    logger.info(f"Uzupełniono rok: {result['year']}")
                
                if not album and result.get('album') and result['album'] not in ['null', 'None', '']:
                    enhanced_metadata['album'] = result['album']
                    logger.info(f"Uzupełniono album: {result['album']}")
                
                # Dodanie informacji o uzupełnieniu
                enhanced_metadata['ai_enhanced'] = True
                enhanced_metadata['ai_confidence'] = result.get('confidence', 0.5)
                enhanced_metadata['ai_reasoning'] = result.get('reasoning', 'Uzupełniono przez ChatGPT')
                
                return enhanced_metadata
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Błąd parsowania odpowiedzi ChatGPT dla metadanych: {e}")
                logger.error(f"Surowa odpowiedź: {ai_response}")
                return metadata
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Błąd podczas uzupełniania metadanych przez ChatGPT: {e}")
            
            # Sprawdzenie czy to błąd quota
            if "insufficient_quota" in error_str or "429" in error_str:
                logger.warning("⚠️ BRAK ŚRODKÓW NA KONCIE OPENAI - ChatGPT zostanie wyłączony dla tej sesji")
                logger.warning("💡 Aby naprawić: https://platform.openai.com/account/billing")
                # Wyłączenie klienta OpenAI dla tej sesji
                self.openai_client = None
            
            return metadata
    
    def _search_spotify(self, artist: str, title: str, album: str = "") -> Optional[Dict]:
        """Wyszukuje utwór w Spotify"""
        token = self._get_spotify_token()
        if not token:
            return None
            
        try:
            # Przygotowanie zapytania
            query = f"artist:{artist} track:{title}"
            if album:
                query += f" album:{album}"
            
            search_url = "https://api.spotify.com/v1/search"
            headers = {'Authorization': f'Bearer {token}'}
            params = {
                'q': query,
                'type': 'track',
                'limit': 1
            }
            
            response = self.session.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            tracks = data.get('tracks', {}).get('items', [])
            
            if not tracks:
                return None
                
            track = tracks[0]
            
            # Pobieranie dodatkowych informacji o utworze
            track_id = track['id']
            audio_features = self._get_spotify_audio_features(track_id, token)
            
            result = {
                'genres': [],
                'year': track['album']['release_date'][:4] if track['album']['release_date'] else '',
                'label': track['album'].get('label', ''),
                'popularity': track.get('popularity', 0)
            }
            
            # Gatunki z artysty
            if track['artists']:
                artist_id = track['artists'][0]['id']
                artist_genres = self._get_spotify_artist_genres(artist_id, token)
                if artist_genres:
                    result['genres'] = artist_genres
            
            # Cechy audio
            if audio_features:
                result.update({
                    'bpm': str(int(audio_features.get('tempo', 0))),
                    'key': self._spotify_key_to_string(audio_features.get('key', -1)),
                    'energy': str(round(audio_features.get('energy', 0), 2)),
                    'danceability': str(round(audio_features.get('danceability', 0), 2)),
                    'valence': str(round(audio_features.get('valence', 0), 2)),
                    'acousticness': str(round(audio_features.get('acousticness', 0), 2))
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania w Spotify: {e}")
            return None
    
    def _get_spotify_audio_features(self, track_id: str, token: str) -> Optional[Dict]:
        """Pobiera cechy audio utworu ze Spotify"""
        try:
            url = f"https://api.spotify.com/v1/audio-features/{track_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania cech audio: {e}")
            return None
    
    def _get_spotify_artist_genres(self, artist_id: str, token: str) -> List[str]:
        """Pobiera gatunki artysty ze Spotify"""
        try:
            url = f"https://api.spotify.com/v1/artists/{artist_id}"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('genres', [])
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania gatunków artysty: {e}")
            return []
    
    def _spotify_key_to_string(self, key: int) -> str:
        """Konwertuje klucz Spotify na string"""
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        if 0 <= key < len(keys):
            return keys[key]
        return ''
    
    def _search_lastfm(self, artist: str, title: str) -> Optional[Dict]:
        """Wyszukuje utwór w Last.fm"""
        if not self.lastfm_api_key:
            return None
            
        try:
            # Wyszukiwanie utworu
            url = "http://ws.audioscrobbler.com/2.0/"
            params = {
                'method': 'track.getInfo',
                'api_key': self.lastfm_api_key,
                'artist': artist,
                'track': title,
                'format': 'json'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'error' in data:
                return None
                
            track = data.get('track', {})
            
            result = {
                'tags': [],
                'genres': []
            }
            
            # Tagi z utworu
            if 'toptags' in track and 'tag' in track['toptags']:
                tags = track['toptags']['tag']
                if isinstance(tags, list):
                    result['tags'] = [tag['name'] for tag in tags[:10]]
                elif isinstance(tags, dict):
                    result['tags'] = [tags['name']]
            
            # Data wydania z albumu
            if 'album' in track and 'wiki' in track['album']:
                wiki = track['album']['wiki']
                if 'published' in wiki:
                    result['year'] = wiki['published'][:4]
            
            # Gatunki z tagów (mapowanie popularnych tagów na gatunki)
            for tag in result['tags']:
                tag_lower = tag.lower()
                if any(genre_word in tag_lower for genre_word in ['electronic', 'techno', 'house', 'ambient', 'trance']):
                    result['genres'].append(tag)
            
            return result
            
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania w Last.fm: {e}")
            return None
    
    def _search_web(self, artist: str, title: str) -> Optional[Dict]:
        """Wyszukuje informacje w internecie (zaawansowane wyszukiwanie)"""
        try:
            results = {'genres': [], 'tags': [], 'additional_info': {}}
            
            # 1. Wyszukiwanie na podstawie słów kluczowych
            search_text = f"{artist} {title}".lower()
            keyword_genres = self._search_by_keywords(search_text)
            if keyword_genres:
                results['genres'].extend(keyword_genres)
            
            # 2. Wyszukiwanie w MusicBrainz
            musicbrainz_info = self._search_musicbrainz(artist, title)
            if musicbrainz_info:
                if musicbrainz_info.get('genres'):
                    results['genres'].extend(musicbrainz_info['genres'])
                if musicbrainz_info.get('tags'):
                    results['tags'].extend(musicbrainz_info['tags'])
            
            # 3. Wyszukiwanie w Discogs (symulowane)
            discogs_info = self._search_discogs_style(artist, title)
            if discogs_info:
                results['genres'].extend(discogs_info)
            
            # 4. Analiza wzorców nazw artystów/utworów
            pattern_genres = self._analyze_name_patterns(artist, title)
            if pattern_genres:
                results['genres'].extend(pattern_genres)
            
            # 5. Wyszukiwanie kontekstowe
            context_genres = self._contextual_search(artist, title)
            if context_genres:
                results['genres'].extend(context_genres)
            
            # Usunięcie duplikatów
            results['genres'] = list(set(results['genres']))
            results['tags'] = list(set(results['tags']))
            
            return results if results['genres'] or results['tags'] else None
                
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania w internecie: {e}")
            
        return None
    
    def _search_by_keywords(self, search_text: str) -> List[str]:
        """Wyszukiwanie na podstawie słów kluczowych"""
        electronic_keywords = {
            'ambient': ['ambient', 'atmospheric', 'drone', 'space', 'calm', 'meditation', 'peaceful'],
            'techno': ['techno', 'minimal', 'detroit', 'hard', 'driving', 'machine', 'industrial'],
            'house': ['house', 'deep house', 'tech house', 'funky', 'groove', 'disco', 'dance'],
            'trance': ['trance', 'progressive', 'uplifting', 'epic', 'emotional', 'euphoric'],
            'dubstep': ['dubstep', 'bass', 'wobble', 'drop', 'heavy', 'aggressive', 'glitch'],
            'drum_and_bass': ['dnb', 'drum and bass', 'jungle', 'breakbeat', 'liquid', 'neurofunk'],
            'industrial': ['industrial', 'ebm', 'harsh', 'dark', 'metal', 'noise', 'distortion'],
            'experimental': ['experimental', 'idm', 'glitch', 'weird', 'strange', 'abstract', 'avant'],
            'synthwave': ['synth', 'retro', '80s', 'neon', 'cyber', 'outrun', 'vaporwave'],
            'downtempo': ['downtempo', 'chillout', 'lounge', 'trip hop', 'slow', 'relaxed']
        }
        
        detected_genres = []
        for genre, keywords in electronic_keywords.items():
            if any(keyword in search_text for keyword in keywords):
                detected_genres.append(genre)
        
        return detected_genres
    
    def _search_musicbrainz(self, artist: str, title: str) -> Optional[Dict]:
        """Wyszukiwanie w MusicBrainz API"""
        try:
            # Symulacja wyszukiwania MusicBrainz (można rozszerzyć o prawdziwe API)
            query = f"{artist} {title}".lower()
            
            # Podstawowe mapowanie na podstawie popularnych artystów/labelów
            label_genre_mapping = {
                'warp': ['experimental', 'idm'],
                'ninja tune': ['downtempo', 'trip_hop'],
                'hospital': ['drum_and_bass'],
                'metalheadz': ['drum_and_bass'],
                'ostgut ton': ['techno'],
                'kompakt': ['minimal', 'techno'],
                'ghostly': ['ambient', 'experimental'],
                'planet mu': ['experimental', 'idm'],
                'raster': ['experimental', 'glitch'],
                'mute': ['industrial', 'experimental']
            }
            
            for label, genres in label_genre_mapping.items():
                if label in query:
                    return {'genres': genres, 'tags': [label]}
            
            return None
            
        except Exception as e:
            logger.warning(f"Błąd MusicBrainz search: {e}")
            return None
    
    def _search_discogs_style(self, artist: str, title: str) -> List[str]:
        """Symulacja wyszukiwania w stylu Discogs"""
        # Analiza wzorców typowych dla różnych gatunków
        text = f"{artist} {title}".lower()
        
        style_patterns = {
            'ambient': ['field recording', 'soundscape', 'meditation', 'nature'],
            'techno': ['berlin', 'detroit', 'acid', 'rave', 'underground'],
            'house': ['chicago', 'garage', 'vocal', 'soulful', 'deep'],
            'trance': ['goa', 'psy', 'progressive', 'uplifting', 'anthem'],
            'industrial': ['power electronics', 'harsh noise', 'dark ambient', 'ebm'],
            'experimental': ['musique concrète', 'electroacoustic', 'sound art', 'noise']
        }
        
        detected = []
        for genre, patterns in style_patterns.items():
            if any(pattern in text for pattern in patterns):
                detected.append(genre)
        
        return detected
    
    def _analyze_name_patterns(self, artist: str, title: str) -> List[str]:
        """Analiza wzorców w nazwach artystów i utworów"""
        patterns = []
        
        # Wzorce w nazwach artystów
        artist_lower = artist.lower()
        if any(word in artist_lower for word in ['ambient', 'drone', 'field']):
            patterns.append('ambient')
        if any(word in artist_lower for word in ['techno', 'minimal', 'acid']):
            patterns.append('techno')
        if any(word in artist_lower for word in ['bass', 'dub', 'step']):
            patterns.append('dubstep')
        
        # Wzorce w tytułach
        title_lower = title.lower()
        if any(word in title_lower for word in ['remix', 'mix', 'edit']):
            # Wykryj styl remiksu z nawiasów: (Techno Remix), (Deep House Mix)
            import re
            m = re.search(r'\(([^)]*?)\)', title_lower)
            remix_hint = m.group(1) if m else ''
            if any(h in remix_hint for h in ['techno', 'acid']):
                patterns.append('techno')
            elif any(h in remix_hint for h in ['trance', 'uplift', 'progressive']):
                patterns.append('trance')
            elif any(h in remix_hint for h in ['deep', 'house', 'garage']):
                patterns.append('house')
            elif any(h in remix_hint for h in ['dub', 'bass', 'step']):
                patterns.append('dubstep')
            else:
                patterns.append('house')  # domyślny
        if any(word in title_lower for word in ['part', 'chapter', 'movement']):
            patterns.append('ambient')  # Długie kompozycje
        
        return patterns
    
    def _contextual_search(self, artist: str, title: str) -> List[str]:
        """Wyszukiwanie kontekstowe na podstawie dodatkowych wskazówek"""
        context_genres = []
        
        # Analiza długości nazw (heurystyka)
        if len(title) > 30:  # Długie tytuły często to ambient/experimental
            context_genres.append('experimental')
        
        # Analiza znaków specjalnych
        if any(char in title for char in ['_', '-', '.']):
            if title.count('_') >= 3:
                context_genres.append('experimental')
        
        # Analiza numerów w tytułach
        import re
        if re.search(r'\d+', title):
            if re.match(r'^\d+$', title.replace('.wav', '').replace('.mp3', '')):
                context_genres.append('minimal')
        
        return context_genres
    
    def search_by_filename(self, filename: str) -> Dict:
        """
        Próbuje wyciągnąć informacje o utworze z nazwy pliku oraz
        wykrywa widoczną strukturę "Artysta - Tytuł"
        
        Args:
            filename: Nazwa pliku
            
        Returns:
            Słownik z wyciągniętymi informacjami
        """
        # Usunięcie rozszerzenia
        name = filename.rsplit('.', 1)[0]
        
        # Typowe separatory
        separators = [' - ', '_', ' – ', ' — ']
        
        artist = ""
        title = ""
        
        # Próba podziału na artystę i tytuł
        structure_detected = False
        for sep in separators:
            if sep in name:
                parts = name.split(sep, 1)
                if len(parts) == 2:
                    artist = parts[0].strip()
                    title = parts[1].strip()
                    structure_detected = True
                    break
        
        # Jeśli nie udało się podzielić, cała nazwa to tytuł
        if not artist and not title:
            title = name.strip()
        
        # Czyszczenie nazw
        artist = self._clean_name(artist)
        title = self._clean_name(title)
        
        return {
            'artist': artist,
            'title': title,
            # True jeśli wykryto strukturę "Artysta - Tytuł"
            'structure_detected': structure_detected,
            # Informacyjnie: funkcja została wykonana
            'filename_parsed': True
        }
    
    def _clean_name(self, name: str) -> str:
        """Czyści nazwę z niepotrzebnych znaków"""
        # Usunięcie nawiasów z dodatkowymi informacjami
        import re
        name = re.sub(r'\\([^)]*\\)', '', name)
        name = re.sub(r'\\[[^\\]]*\\]', '', name)
        
        # Usunięcie numerów tracków
        name = re.sub(r'^\\d+\\.?\\s*', '', name)
        
        return name.strip()
    
    def _ai_powered_analysis(self, artist: str, title: str, filename: str = "") -> Optional[Dict]:
        """
        Prawdziwa analiza AI przy użyciu ChatGPT API dla szczegółowej klasyfikacji gatunków
        
        Args:
            artist: Nazwa artysty
            title: Tytuł utworu
            filename: Nazwa pliku (opcjonalne)
            
        Returns:
            Słownik z wynikami analizy AI
        """
        try:
            if not self.openai_client:
                logger.warning("OpenAI API niedostępne - pomijam analizę AI")
                return None
            
            # Przygotowanie promptu dla ChatGPT
            prompt = f"""
Przeanalizuj następujący utwór muzyczny i określ jego gatunek:

Artysta: {artist}
Tytuł: {title}
Nazwa pliku: {filename if filename else 'brak'}

Proszę o szczegółową analizę i podanie:
1. Główny gatunek muzyczny (primary_genre)
2. Gatunek drugorzędny jeśli istnieje (secondary_genre)
3. Poziom pewności (0.0-1.0)
4. Lista tagów opisujących utwór (maksymalnie 5)
5. Krótkie uzasadnienie klasyfikacji
6. Przybliżone BPM utworu (bpm) jeśli znane lub można oszacować
7. Czy utwór jest remiksem (is_remix: true/false)
8. Styl remiksu (remix_style), jeśli dotyczy

Skup się szczególnie na:
- Muzyce elektronicznej (ambient, techno, house, trance, experimental, industrial, etc.)
- Podgatunkach i niszowych stylach
- Kontekście artysty i jego twórczości
- Charakterystycznych elementach tytułu
 - Charakterystycznych elementach tytułu
 - Jeśli utwór jest remiksem, klasyfikację gatunku opieraj na stylu remiksu (remix_style), a nie oryginale.

Odpowiedz w formacie JSON:
{{
    "primary_genre": "nazwa_gatunku",
    "secondary_genre": "nazwa_gatunku_lub_null",
    "confidence": 0.85,
    "tags": ["tag1", "tag2", "tag3"],
    "reasoning": "krótkie uzasadnienie",
    "bpm": 128,
    "is_remix": false,
    "remix_style": "house"
}}
"""

            # Zapytanie do ChatGPT
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system", 
                        "content": "Jesteś ekspertem od klasyfikacji gatunków muzycznych, szczególnie muzyki elektronicznej. Odpowiadaj zawsze w formacie JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parsowanie odpowiedzi
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"Odpowiedź ChatGPT dla '{artist} - {title}': {ai_response}")
            
            # Próba parsowania JSON
            try:
                # Usunięcie ewentualnych znaczników markdown
                if ai_response.startswith('```json'):
                    ai_response = ai_response[7:]
                if ai_response.endswith('```'):
                    ai_response = ai_response[:-3]
                
                result = json.loads(ai_response.strip())
                
                # Walidacja wyników
                if not isinstance(result, dict):
                    raise ValueError("Odpowiedź nie jest słownikiem")
                
                # Sprawdzenie wymaganych pól
                required_fields = ['primary_genre', 'confidence']
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Brak wymaganego pola: {field}")
                
                # Normalizacja confidence
                confidence = float(result.get('confidence', 0.5))
                confidence = max(0.0, min(1.0, confidence))
                
                # Przygotowanie finalnego wyniku
                final_result = {
                    'primary_genre': str(result.get('primary_genre', '')).lower().replace(' ', '_'),
                    'secondary_genre': str(result.get('secondary_genre', '')).lower().replace(' ', '_') if result.get('secondary_genre') else None,
                    'confidence': confidence,
                    'tags': result.get('tags', [])[:5],  # Maksymalnie 5 tagów
                    'analysis_method': 'chatgpt_api',
                    'reasoning': result.get('reasoning', 'Analiza ChatGPT'),
                    'bpm': result.get('bpm'),
                    'is_remix': bool(result.get('is_remix', False)),
                    'remix_style': result.get('remix_style')
                }
                
                # Usunięcie pustych wartości
                if final_result['secondary_genre'] in ['', 'null', 'none']:
                    final_result['secondary_genre'] = None
                
                logger.info(f"Pomyślna analiza ChatGPT: {final_result['primary_genre']} (pewność: {confidence:.2f})")
                return final_result
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Błąd parsowania odpowiedzi ChatGPT: {e}")
                logger.error(f"Surowa odpowiedź: {ai_response}")
                
                # Fallback - próba wyciągnięcia gatunku z tekstu
                return self._parse_ai_response_fallback(ai_response, artist, title)
                
        except Exception as e:
            error_str = str(e)
            logger.error(f"Błąd podczas zapytania do ChatGPT: {e}")
            
            # Sprawdzenie czy to błąd quota
            if "insufficient_quota" in error_str or "429" in error_str:
                logger.warning("⚠️ BRAK ŚRODKÓW NA KONCIE OPENAI - ChatGPT zostanie wyłączony dla tej sesji")
                logger.warning("💡 Aby naprawić: https://platform.openai.com/account/billing")
                # Wyłączenie klienta OpenAI dla tej sesji
                self.openai_client = None
            
            return None
    
    def _parse_ai_response_fallback(self, response_text: str, artist: str, title: str) -> Optional[Dict]:
        """
        Fallback parsing gdy ChatGPT nie zwrócił poprawnego JSON
        """
        try:
            response_lower = response_text.lower()
            
            # Lista popularnych gatunków do wyszukania w tekście
            genres = [
                'ambient', 'techno', 'house', 'trance', 'experimental', 'industrial',
                'drum_and_bass', 'dubstep', 'breakbeat', 'garage', 'downtempo',
                'hardcore', 'minimal', 'progressive', 'dark_ambient', 'psytrance'
            ]
            
            found_genre = None
            for genre in genres:
                if genre in response_lower:
                    found_genre = genre
                    break
            
            # Heurystyka BPM: znajdź liczby 60-200 w tekście
            bpm = None
            try:
                import re
                nums = re.findall(r"(\d{2,3})", response_lower)
                for n in nums:
                    val = int(n)
                    if 60 <= val <= 200:
                        bpm = val
                        break
            except Exception:
                bpm = None

            # Heurystyka remiksu
            is_remix = any(k in response_lower for k in ['remix', 'mix', 'edit'])
            remix_style = None
            if is_remix:
                for hint, style in [
                    ('techno', 'techno'),
                    ('acid', 'techno'),
                    ('trance', 'trance'),
                    ('uplift', 'trance'),
                    ('progressive', 'trance'),
                    ('deep', 'house'),
                    ('garage', 'house'),
                    ('house', 'house'),
                    ('dub', 'dubstep'),
                    ('bass', 'dubstep'),
                    ('step', 'dubstep')
                ]:
                    if hint in response_lower:
                        remix_style = style
                        break

            if found_genre:
                return {
                    'primary_genre': found_genre,
                    'secondary_genre': None,
                    'confidence': 0.6,  # Średnia pewność dla fallback
                    'tags': [found_genre],
                    'analysis_method': 'chatgpt_fallback',
                    'reasoning': f"Fallback parsing znalazł gatunek: {found_genre}",
                    'bpm': bpm,
                    'is_remix': is_remix,
                    'remix_style': remix_style
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Błąd w fallback parsing: {e}")
            return None