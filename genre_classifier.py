"""
System klasyfikacji gatunków muzyki elektronicznej
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from collections import Counter

from config import ELECTRONIC_GENRES, GENRE_KEYWORDS, MIN_CONFIDENCE_SCORE

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GenreClassifier:
    """Klasa do klasyfikacji gatunków muzyki elektronicznej"""
    
    def __init__(self):
        self.electronic_genres = ELECTRONIC_GENRES
        self.genre_keywords = GENRE_KEYWORDS
        self.min_confidence = MIN_CONFIDENCE_SCORE
        
        # Rozszerzone mapowanie gatunków
        self.genre_mapping = self._build_genre_mapping()
        
        # Wzorce BPM dla różnych gatunków
        self.bpm_ranges = {
            'ambient': (60, 90),
            'downtempo': (70, 100),
            'house': (120, 130),
            'techno': (120, 150),
            'trance': (130, 140),
            'drum_and_bass': (160, 180),
            'hardcore': (160, 200),
            'dubstep': (140, 150),
            'breakbeat': (130, 150)
        }
    
    def classify_track(self, metadata: Dict, web_info: Dict = None) -> Dict:
        """
        Klasyfikuje gatunek utworu na podstawie dostępnych informacji
        
        Args:
            metadata: Metadane z pliku
            web_info: Informacje z internetu
            
        Returns:
            Słownik z wynikami klasyfikacji
        """
        classification_result = {
            'primary_genre': 'unknown',
            'secondary_genres': [],
            'confidence_score': 0.0,
            'classification_sources': [],
            'suggested_folder': 'Other',
            'analysis_details': {}
        }
        
        # Zbieranie wszystkich dostępnych informacji
        all_info = self._gather_all_info(metadata, web_info)
        
        # Różne metody klasyfikacji
        genre_scores = {}
        
        # 1. Klasyfikacja na podstawie tagów gatunku
        genre_tag_scores = self._classify_by_genre_tags(all_info)
        self._merge_scores(genre_scores, genre_tag_scores, 'genre_tags')
        
        # 2. Klasyfikacja na podstawie słów kluczowych
        keyword_scores = self._classify_by_keywords(all_info)
        self._merge_scores(genre_scores, keyword_scores, 'keywords')
        
        # 3. Klasyfikacja na podstawie BPM
        bpm_scores = self._classify_by_bpm(all_info.get('bpm', ''))
        self._merge_scores(genre_scores, bpm_scores, 'bpm')
        
        # 4. Klasyfikacja na podstawie cech audio (Spotify)
        audio_scores = self._classify_by_audio_features(all_info)
        self._merge_scores(genre_scores, audio_scores, 'audio_features')
        
        # 4b. Klasyfikacja na podstawie lokalnej analizy audio
        local_audio_scores = self._classify_by_local_audio_analysis(all_info)
        self._merge_scores(genre_scores, local_audio_scores, 'local_audio')
        
        # 4c. Klasyfikacja na podstawie analizy AI
        ai_scores = self._classify_by_ai_analysis(all_info)
        self._merge_scores(genre_scores, ai_scores, 'ai_analysis')
        
        # 5. Klasyfikacja na podstawie nazwy pliku/artysty
        filename_scores = self._classify_by_filename(all_info)
        self._merge_scores(genre_scores, filename_scores, 'filename')
        
        # Obliczanie końcowych wyników
        if genre_scores:
            # Sortowanie według wyniku
            sorted_genres = sorted(genre_scores.items(), key=lambda x: x[1]['total_score'], reverse=True)
            
            primary_genre, primary_data = sorted_genres[0]
            classification_result['primary_genre'] = primary_genre
            classification_result['confidence_score'] = primary_data['total_score']
            classification_result['classification_sources'] = primary_data['sources']
            
            # Gatunki drugorzędne
            secondary = [genre for genre, data in sorted_genres[1:3] 
                        if data['total_score'] > 0.3]
            classification_result['secondary_genres'] = secondary
            
            # Sugerowany folder
            classification_result['suggested_folder'] = self._get_folder_name(primary_genre)
            
            # Szczegóły analizy
            classification_result['analysis_details'] = {
                'all_scores': {genre: data['total_score'] for genre, data in sorted_genres},
                'score_breakdown': {genre: data for genre, data in sorted_genres[:3]}
            }
        
        return classification_result
    
    def _gather_all_info(self, metadata: Dict, web_info: Dict = None) -> Dict:
        """Zbiera wszystkie dostępne informacje o utworze"""
        all_info = {
            'title': metadata.get('title', ''),
            'artist': metadata.get('artist', ''),
            'album': metadata.get('album', ''),
            'genres': metadata.get('genre', []),
            'bpm': metadata.get('bpm', ''),
            'year': metadata.get('year', ''),
            'filename': metadata.get('filename', ''),
            'file_path': metadata.get('file_path', ''),
            'tags': []
        }
        
        # Dodaj informacje z internetu (nowy format)
        if web_info:
            # Obsługa nowego formatu z primary_genre i confidence
            if 'primary_genre' in web_info:
                if web_info['primary_genre'] != 'unknown':
                    all_info['web_primary_genre'] = web_info['primary_genre']
                    all_info['web_confidence'] = web_info.get('confidence', 0.0)
                
                if web_info.get('secondary_genre'):
                    all_info['web_secondary_genre'] = web_info['secondary_genre']
            
            # Standardowe informacje
            all_info.update({
                'web_genres': web_info.get('genres', []),
                'web_tags': web_info.get('tags', []),
                'energy': web_info.get('energy', ''),
                'danceability': web_info.get('danceability', ''),
                'valence': web_info.get('valence', ''),
                'acousticness': web_info.get('acousticness', ''),
                'web_bpm': web_info.get('bpm', '')
            })
            
            # Dodatkowe informacje z AI analysis
            if 'additional_info' in web_info:
                additional = web_info['additional_info']
                
                # Informacje z analizy AI
                if 'ai_analysis' in additional:
                    ai_data = additional['ai_analysis']
                    all_info['ai_genre'] = ai_data.get('primary_genre')
                    all_info['ai_confidence'] = ai_data.get('confidence', 0.0)
                    all_info['ai_tags'] = ai_data.get('tags', [])
                    all_info['ai_reasoning'] = ai_data.get('reasoning', '')
                    # Nowe pola: BPM i remiks
                    if ai_data.get('bpm'):
                        all_info['ai_bpm'] = ai_data.get('bpm')
                    all_info['is_remix'] = bool(ai_data.get('is_remix', False))
                    if ai_data.get('remix_style'):
                        all_info['remix_style'] = str(ai_data.get('remix_style')).lower().replace(' ', '_')
                
                # Informacje z różnych źródeł
                for source in ['spotify', 'lastfm', 'web']:
                    if source in additional:
                        source_data = additional[source]
                        if source_data.get('genres'):
                            all_info[f'{source}_genres'] = source_data['genres']
                        if source_data.get('tags'):
                            all_info[f'{source}_tags'] = source_data['tags']
            
            # Użyj BPM z internetu jeśli nie ma w metadanych
            if not all_info.get('bpm') and web_info.get('bpm'):
                all_info['bpm'] = web_info['bpm']
            # Użyj BPM z AI jeśli nie ma w metadanych ani w web_info
            if not all_info.get('bpm') and all_info.get('ai_bpm'):
                all_info['bpm'] = all_info['ai_bpm']
        
        return all_info
    
    def _classify_by_genre_tags(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie tagów gatunku z różnych źródeł"""
        scores = {}
        
        # Zbierz gatunki z różnych źródeł
        all_genres = []
        
        # Gatunki z metadanych
        metadata_genres = all_info.get('genres', [])
        if isinstance(metadata_genres, str):
            metadata_genres = [metadata_genres]
        all_genres.extend([(g, 'metadata', 0.9) for g in metadata_genres])
        
        # Gatunki z internetu
        web_genres = all_info.get('web_genres', [])
        all_genres.extend([(g, 'web', 0.7) for g in web_genres])
        
        # Gatunki z różnych źródeł internetowych
        for source in ['spotify', 'lastfm', 'web']:
            source_genres = all_info.get(f'{source}_genres', [])
            weight = {'spotify': 0.8, 'lastfm': 0.6, 'web': 0.5}.get(source, 0.5)
            all_genres.extend([(g, source, weight) for g in source_genres])
        
        # Przetwarzaj wszystkie gatunki
        for genre, source, weight in all_genres:
            if not genre:
                continue
                
            genre_lower = genre.lower()
            
            # Bezpośrednie dopasowanie
            for main_genre, subgenres in self.electronic_genres.items():
                if genre_lower in [sg.lower() for sg in subgenres]:
                    if main_genre not in scores:
                        scores[main_genre] = {'score': 0, 'sources': []}
                    scores[main_genre]['score'] += weight
                    scores[main_genre]['sources'].append(f"direct_match_{source}:{genre}")
            
            # Dopasowanie przez mapowanie
            mapped_genre = self._map_genre(genre_lower)
            if mapped_genre:
                if mapped_genre not in scores:
                    scores[mapped_genre] = {'score': 0, 'sources': []}
                scores[mapped_genre]['score'] += weight * 0.8
                scores[mapped_genre]['sources'].append(f"mapped_{source}:{genre}")
        
        return scores
    
    def _classify_by_keywords(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie słów kluczowych"""
        scores = {}
        
        # Tekst do analizy
        text_fields = [
            all_info.get('title', ''),
            all_info.get('artist', ''),
            all_info.get('album', ''),
            all_info.get('genre', ''),
            all_info.get('comment', ''),
            ' '.join(all_info.get('tags', []))
        ]
        
        search_text = ' '.join(text_fields).lower()
        
        for genre, keywords in self.genre_keywords.items():
            genre_score = 0
            found_keywords = []
            
            for keyword in keywords:
                if keyword in search_text:
                    genre_score += 0.3
                    found_keywords.append(keyword)
            
            if genre_score > 0:
                scores[genre] = {
                    'score': min(genre_score, 1.0),
                    'sources': [f"keywords:{','.join(found_keywords)}"]
                }
        
        return scores
    
    def _classify_by_bpm(self, bpm_str: str) -> Dict:
        """Klasyfikacja na podstawie BPM"""
        scores = {}
        
        try:
            bpm = float(bpm_str) if bpm_str else 0
            if bpm == 0:
                return scores
                
            for genre, (min_bpm, max_bpm) in self.bpm_ranges.items():
                if min_bpm <= bpm <= max_bpm:
                    # Im bliżej środka zakresu, tym wyższy wynik
                    center = (min_bpm + max_bpm) / 2
                    distance = abs(bpm - center)
                    max_distance = (max_bpm - min_bpm) / 2
                    score = 1.0 - (distance / max_distance)
                    
                    scores[genre] = {
                        'score': score * 0.6,  # BPM ma średnią wagę
                        'sources': [f"bpm:{bpm}"]
                    }
        
        except (ValueError, TypeError):
            pass
        
        return scores
    
    def _classify_by_audio_features(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie cech audio ze Spotify"""
        scores = {}
        
        try:
            energy = float(all_info.get('energy', 0))
            danceability = float(all_info.get('danceability', 0))
            valence = float(all_info.get('valence', 0))
            acousticness = float(all_info.get('acousticness', 0))
            
            # Reguły klasyfikacji na podstawie cech audio
            if energy > 0.8 and danceability > 0.7:
                scores['techno'] = {'score': 0.5, 'sources': ['high_energy_dance']}
            
            if energy < 0.3 and valence < 0.4:
                scores['ambient'] = {'score': 0.6, 'sources': ['low_energy_valence']}
            
            if danceability > 0.8 and energy > 0.6:
                scores['house'] = {'score': 0.4, 'sources': ['high_danceability']}
            
            if acousticness < 0.1 and energy > 0.7:
                scores['electronic'] = {'score': 0.3, 'sources': ['electronic_features']}
            
        except (ValueError, TypeError):
            pass
        
        return scores
    
    def _classify_by_local_audio_analysis(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie lokalnej analizy audio"""
        scores = {}
        
        try:
            file_path = all_info.get('file_path', '')
            if not file_path:
                return scores
            
            # Próba importu librosa dla analizy audio
            try:
                import librosa
                import numpy as np
            except ImportError:
                logger.warning("Librosa nie jest zainstalowana - pomijam analizę audio")
                return scores
            
            # Ładowanie audio (pierwsze 30 sekund dla szybkości)
            try:
                y, sr = librosa.load(file_path, duration=30, sr=22050)
            except Exception as e:
                logger.warning(f"Nie można załadować pliku audio {file_path}: {e}")
                return scores
            
            # Analiza tempa
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Konwersja numpy array na float
            tempo = float(tempo) if hasattr(tempo, 'item') else float(tempo)
            
            # Analiza spektralnych cech
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # Obliczanie średnich
            avg_spectral_centroid = float(np.mean(spectral_centroids))
            avg_spectral_rolloff = float(np.mean(spectral_rolloff))
            avg_zcr = float(np.mean(zero_crossing_rate))
            
            # Klasyfikacja na podstawie tempa
            if tempo < 90:
                scores['ambient'] = {'score': 0.3, 'sources': [f'slow_tempo:{tempo:.1f}']}
            elif 90 <= tempo < 110:
                scores['downtempo'] = {'score': 0.2, 'sources': [f'medium_tempo:{tempo:.1f}']}
            elif 110 <= tempo < 130:
                scores['house'] = {'score': 0.3, 'sources': [f'house_tempo:{tempo:.1f}']}
            elif 130 <= tempo < 150:
                scores['techno'] = {'score': 0.3, 'sources': [f'techno_tempo:{tempo:.1f}']}
            elif 150 <= tempo < 180:
                scores['drum_and_bass'] = {'score': 0.3, 'sources': [f'fast_tempo:{tempo:.1f}']}
            else:
                scores['hardcore'] = {'score': 0.2, 'sources': [f'very_fast_tempo:{tempo:.1f}']}
            
            # Klasyfikacja na podstawie spektralnych cech
            if avg_spectral_centroid < 1000:
                # Niskie częstotliwości dominują
                if 'ambient' not in scores:
                    scores['ambient'] = {'score': 0, 'sources': []}
                scores['ambient']['score'] += 0.2
                scores['ambient']['sources'].append('low_frequencies')
            elif avg_spectral_centroid > 3000:
                # Wysokie częstotliwości dominują
                if 'techno' not in scores:
                    scores['techno'] = {'score': 0, 'sources': []}
                scores['techno']['score'] += 0.2
                scores['techno']['sources'].append('high_frequencies')
            
            # Analiza dynamiki (zero crossing rate)
            if avg_zcr > 0.1:
                # Wysoka dynamika = energetyczna muzyka
                if 'electronic' not in scores:
                    scores['electronic'] = {'score': 0, 'sources': []}
                scores['electronic']['score'] += 0.15
                scores['electronic']['sources'].append('high_dynamics')
            
        except Exception as e:
            logger.warning(f"Błąd podczas analizy audio: {e}")
        
        return scores
    
    def _classify_by_ai_analysis(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie analizy AI"""
        scores = {}
        
        # Sprawdź czy mamy wyniki analizy AI
        ai_genre = all_info.get('ai_genre')
        ai_confidence = all_info.get('ai_confidence', 0.0)
        ai_tags = all_info.get('ai_tags', [])
        
        if ai_genre and ai_confidence > 0.3:
            # Główny gatunek z AI
            if ai_genre not in scores:
                scores[ai_genre] = {'score': 0, 'sources': []}
            
            # Wysokie zaufanie do analizy AI
            scores[ai_genre]['score'] += ai_confidence * 1.2  # Boost dla AI
            scores[ai_genre]['sources'].append(f"ai_primary:{ai_confidence:.2f}")
            
            # Dodaj punkty za tagi AI
            for tag in ai_tags:
                tag_lower = tag.lower()
                mapped_genre = self._map_genre(tag_lower)
                if mapped_genre:
                    if mapped_genre not in scores:
                        scores[mapped_genre] = {'score': 0, 'sources': []}
                    scores[mapped_genre]['score'] += 0.3
                    scores[mapped_genre]['sources'].append(f"ai_tag:{tag}")

        # Jeśli to remiks, preferuj styl remiksu nad oryginał
        if all_info.get('is_remix'):
            remix_style = all_info.get('remix_style')
            if remix_style:
                mapped_remix = self._map_genre(remix_style)
                target_genre = mapped_remix or remix_style
                if target_genre not in scores:
                    scores[target_genre] = {'score': 0, 'sources': []}
                scores[target_genre]['score'] += 0.8
                scores[target_genre]['sources'].append('ai_remix_style')
        
        # Sprawdź informacje z web primary genre
        web_primary = all_info.get('web_primary_genre')
        web_confidence = all_info.get('web_confidence', 0.0)
        
        if web_primary and web_confidence > 0.4:
            if web_primary not in scores:
                scores[web_primary] = {'score': 0, 'sources': []}
            scores[web_primary]['score'] += web_confidence
            scores[web_primary]['sources'].append(f"web_primary:{web_confidence:.2f}")
        
        # Sprawdź secondary genre
        web_secondary = all_info.get('web_secondary_genre')
        if web_secondary:
            if web_secondary not in scores:
                scores[web_secondary] = {'score': 0, 'sources': []}
            scores[web_secondary]['score'] += 0.4
            scores[web_secondary]['sources'].append("web_secondary")
        
        return scores
    
    def _classify_by_filename(self, all_info: Dict) -> Dict:
        """Klasyfikacja na podstawie nazwy pliku i ścieżki"""
        scores = {}
        
        filename = all_info.get('filename', '').lower()
        file_path = all_info.get('file_path', '').lower()
        
        # Sprawdzanie ścieżki pliku
        for genre in self.electronic_genres.keys():
            if genre in file_path or genre in filename:
                scores[genre] = {'score': 0.4, 'sources': [f"path_contains:{genre}"]}
        
        # Rozszerzone wzorce dla różnych gatunków
        patterns = {
            'ambient': [r'amb', r'drone', r'atmospheric', r'space', r'calm', r'meditation', 
                       r'peaceful', r'relax', r'chill', r'soft', r'quiet', r'gentle'],
            'techno': [r'tech', r'minimal', r'detroit', r'hard', r'driving', r'industrial',
                      r'machine', r'robot', r'cyber', r'digital', r'electronic'],
            'house': [r'house', r'deep', r'funky', r'groove', r'disco', r'dance',
                     r'club', r'party', r'beat', r'rhythm'],
            'trance': [r'trance', r'uplifting', r'progressive', r'epic', r'emotional',
                      r'euphoric', r'energy', r'psych', r'goa'],
            'dubstep': [r'dub', r'bass', r'wobble', r'drop', r'heavy', r'aggressive',
                       r'distorted', r'glitch', r'step'],
            # Industrial (ogólne)
            'industrial': [r'industrial', r'ebm', r'dark', r'metal', r'noise', r'distortion', r'aggressive', r'mechanical'],
            # Podgatunki Industrial Ambient
            'ambient_industrial': [r'ambient\s*industrial', r'industrial\s*ambient'],
            'death_industrial': [r'death\s*industrial'],
            'power_noise': [r'power\s*noise', r'rhythmic\s*noise', r'power\s*electronics', r'harsh\s*noise'],
            'drum_and_bass': [r'dnb', r'drum', r'bass', r'jungle', r'breakbeat', r'liquid',
                             r'neurofunk', r'jump', r'break'],
            'synthwave': [r'synth', r'retro', r'80s', r'neon', r'cyber', r'outrun',
                         r'vaporwave', r'nostalgic', r'vintage'],
            'experimental': [r'experimental', r'weird', r'strange', r'abstract', r'avant',
                           r'unconventional', r'unique', r'odd', r'unusual']
        }
        
        # Wzorce numeryczne i strukturalne
        numeric_patterns = {
            'minimal': [r'^\d+$', r'^\d+[a-z]?$'],  # Same liczby jak "925"
            'experimental': [r'[_\-]{2,}', r'[a-z]+_[a-z]+_[a-z]+'],  # Wiele podkreśleń
            'ambient': [r'long', r'extended', r'part\d+', r'chapter'],
            'techno': [r'mix\d+', r'set\d+', r'track\d+']
        }
        
        # Sprawdzanie wzorców tekstowych
        for genre, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, filename):
                    if genre not in scores:
                        scores[genre] = {'score': 0, 'sources': []}
                    scores[genre]['score'] += 0.15
                    scores[genre]['sources'].append(f"filename_pattern:{pattern}")
        
        # Sprawdzanie wzorców numerycznych i strukturalnych
        for genre, pattern_list in numeric_patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, filename):
                    if genre not in scores:
                        scores[genre] = {'score': 0, 'sources': []}
                    scores[genre]['score'] += 0.1
                    scores[genre]['sources'].append(f"structure_pattern:{pattern}")
        
        # Analiza długości nazwy pliku (heurystyka)
        if len(filename) < 10:  # Krótkie nazwy często to minimal/experimental
            for genre in ['minimal', 'experimental']:
                if genre not in scores:
                    scores[genre] = {'score': 0.05, 'sources': ['short_filename']}
                else:
                    scores[genre]['score'] += 0.05
        
        # Analiza separatorów
        if '_' in filename:
            separator_count = filename.count('_')
            if separator_count >= 3:  # Wiele separatorów = experimental
                if 'experimental' not in scores:
                    scores['experimental'] = {'score': 0.1, 'sources': ['many_separators']}
                else:
                    scores['experimental']['score'] += 0.1
        
        return scores
    
    def _merge_scores(self, main_scores: Dict, new_scores: Dict, source_type: str):
        """Łączy wyniki z różnych metod klasyfikacji"""
        for genre, data in new_scores.items():
            if genre not in main_scores:
                main_scores[genre] = {'total_score': 0, 'sources': [], 'breakdown': {}}
            
            main_scores[genre]['total_score'] += data['score']
            main_scores[genre]['sources'].extend(data['sources'])
            main_scores[genre]['breakdown'][source_type] = data['score']
    
    def _build_genre_mapping(self) -> Dict:
        """Buduje mapowanie różnych nazw gatunków na główne kategorie"""
        mapping = {}
        
        # Mapowanie popularnych nazw na główne gatunki
        genre_aliases = {
            'ambient': ['chillout', 'new age', 'meditation', 'relaxing'],
            'techno': ['electronic dance', 'edm', 'club', 'rave'],
            'house': ['deep house', 'tech house', 'progressive house'],
            'trance': ['progressive trance', 'uplifting trance', 'psytrance'],
            'dubstep': ['brostep', 'future bass', 'bass music'],
            'drum_and_bass': ['dnb', 'jungle', 'liquid dnb'],
            # Rozszerzone aliasy dla industrial i ambient dark
            'industrial': [
                'ebm', 'dark electronic', 'harsh',
                'industrial ambient', 'ambient industrial', 'death industrial',
                'power noise', 'power electronics', 'rhythmic noise', 'harsh noise'
            ],
            'experimental': ['idm', 'glitch', 'abstract', 'avant-garde']
        }
        
        for main_genre, aliases in genre_aliases.items():
            for alias in aliases:
                mapping[alias.lower()] = main_genre
        
        return mapping
    
    def _map_genre(self, genre: str) -> Optional[str]:
        """Mapuje gatunek na główną kategorię"""
        genre_lower = genre.lower()
        
        # Bezpośrednie mapowanie
        if genre_lower in self.genre_mapping:
            return self.genre_mapping[genre_lower]
        
        # Częściowe dopasowanie
        for mapped_genre, main_genre in self.genre_mapping.items():
            if mapped_genre in genre_lower or genre_lower in mapped_genre:
                return main_genre
        
        return None
    
    def _get_folder_name(self, genre: str) -> str:
        """Zwraca nazwę folderu dla gatunku korzystając z konfiguracji"""
        try:
            # Użyj centralnego mapowania z config, które zawiera podgatunki
            from config import get_genre_folder_name
            return get_genre_folder_name(genre)
        except Exception:
            # Awaryjnie zwróć tytułową nazwę gatunku zamiast "Other Electronic"
            return (genre or 'Unknown').title()
    
    def get_genre_statistics(self, classifications: List[Dict]) -> Dict:
        """Generuje statystyki klasyfikacji"""
        if not classifications:
            return {}
        
        genre_counts = Counter()
        confidence_scores = []
        
        for classification in classifications:
            genre = classification.get('primary_genre', 'unknown')
            confidence = classification.get('confidence_score', 0)
            
            genre_counts[genre] += 1
            confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'total_tracks': len(classifications),
            'genre_distribution': dict(genre_counts),
            'average_confidence': round(avg_confidence, 2),
            'high_confidence_tracks': len([s for s in confidence_scores if s > 0.7]),
            'low_confidence_tracks': len([s for s in confidence_scores if s < 0.3])
        }