"""
Moduł do analizy metadanych plików muzycznych
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mutagen import File
from mutagen.id3 import ID3NoHeaderError
import eyed3

from config import SUPPORTED_FORMATS

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataAnalyzer:
    """Klasa do analizy metadanych plików muzycznych"""
    
    def __init__(self):
        self.supported_formats = SUPPORTED_FORMATS
        
    def extract_metadata(self, file_path: Path) -> Dict:
        """
        Wyciąga metadane z pliku muzycznego
        
        Args:
            file_path: Ścieżka do pliku muzycznego
            
        Returns:
            Słownik z metadanymi
        """
        if not self._is_supported_format(file_path):
            logger.warning(f"Nieobsługiwany format pliku: {file_path}")
            return {}
            
        try:
            # Próba użycia mutagen
            metadata = self._extract_with_mutagen(file_path)
            
            # Jeśli mutagen nie zadziałał, spróbuj eyed3 dla MP3
            if not metadata and file_path.suffix.lower() == '.mp3':
                metadata = self._extract_with_eyed3(file_path)
                
            # Dodaj informacje o pliku
            metadata.update(self._get_file_info(file_path))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Błąd podczas analizy {file_path}: {e}")
            return self._get_file_info(file_path)
    
    def _extract_with_mutagen(self, file_path: Path) -> Dict:
        """Wyciąga metadane używając biblioteki mutagen"""
        try:
            audio_file = File(str(file_path))
            if audio_file is None:
                return {}
                
            metadata = {}
            
            # Podstawowe informacje
            if hasattr(audio_file, 'info'):
                metadata['duration'] = getattr(audio_file.info, 'length', 0)
                metadata['bitrate'] = getattr(audio_file.info, 'bitrate', 0)
                metadata['sample_rate'] = getattr(audio_file.info, 'sample_rate', 0)
                metadata['channels'] = getattr(audio_file.info, 'channels', 0)
            
            # Tagi
            if audio_file.tags:
                metadata['title'] = self._get_tag_value(audio_file.tags, ['TIT2', 'TITLE', '\\xa9nam'])
                metadata['artist'] = self._get_tag_value(audio_file.tags, ['TPE1', 'ARTIST', '\\xa9ART'])
                metadata['album'] = self._get_tag_value(audio_file.tags, ['TALB', 'ALBUM', '\\xa9alb'])
                metadata['genre'] = self._get_tag_value(audio_file.tags, ['TCON', 'GENRE', '\\xa9gen'])
                metadata['year'] = self._get_tag_value(audio_file.tags, ['TDRC', 'DATE', '\\xa9day'])
                metadata['track'] = self._get_tag_value(audio_file.tags, ['TRCK', 'TRACKNUMBER', 'trkn'])
                metadata['albumartist'] = self._get_tag_value(audio_file.tags, ['TPE2', 'ALBUMARTIST', 'aART'])
                metadata['comment'] = self._get_tag_value(audio_file.tags, ['COMM', 'COMMENT', '\\xa9cmt'])
                metadata['bpm'] = self._get_tag_value(audio_file.tags, ['TBPM', 'BPM', 'tmpo'])
                
            return metadata
            
        except Exception as e:
            logger.error(f"Błąd mutagen dla {file_path}: {e}")
            return {}
    
    def _extract_with_eyed3(self, file_path: Path) -> Dict:
        """Wyciąga metadane z MP3 używając eyed3"""
        try:
            audio_file = eyed3.load(str(file_path))
            if audio_file is None or audio_file.tag is None:
                return {}
                
            metadata = {}
            
            # Informacje o pliku
            if audio_file.info:
                metadata['duration'] = audio_file.info.time_secs
                metadata['bitrate'] = audio_file.info.bit_rate[1] if audio_file.info.bit_rate else 0
                metadata['sample_rate'] = audio_file.info.sample_freq
                metadata['channels'] = 2 if audio_file.info.mode == 'Stereo' else 1
            
            # Tagi
            tag = audio_file.tag
            metadata['title'] = tag.title or ''
            metadata['artist'] = tag.artist or ''
            metadata['album'] = tag.album or ''
            metadata['genre'] = tag.genre.name if tag.genre else ''
            metadata['year'] = str(tag.recording_date.year) if tag.recording_date else ''
            metadata['track'] = str(tag.track_num[0]) if tag.track_num and tag.track_num[0] else ''
            metadata['albumartist'] = tag.album_artist or ''
            metadata['comment'] = tag.comments.get('').text if tag.comments else ''
            metadata['bpm'] = str(tag.bpm) if tag.bpm else ''
            
            return metadata
            
        except Exception as e:
            logger.error(f"Błąd eyed3 dla {file_path}: {e}")
            return {}
    
    def _get_tag_value(self, tags, possible_keys: List[str]) -> str:
        """Pobiera wartość tagu z różnych możliwych kluczy"""
        for key in possible_keys:
            if key in tags:
                value = tags[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return ''
    
    def _get_file_info(self, file_path: Path) -> Dict:
        """Pobiera podstawowe informacje o pliku"""
        try:
            stat = file_path.stat()
            return {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_size': stat.st_size,
                'file_extension': file_path.suffix.lower(),
                'modified_time': stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Błąd podczas pobierania informacji o pliku {file_path}: {e}")
            return {
                'filename': file_path.name,
                'file_path': str(file_path),
                'file_extension': file_path.suffix.lower()
            }
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Sprawdza czy format pliku jest obsługiwany"""
        return file_path.suffix.lower() in self.supported_formats
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Path]:
        """
        Skanuje katalog w poszukiwaniu plików muzycznych
        
        Args:
            directory: Katalog do przeskanowania
            recursive: Czy skanować rekurencyjnie
            
        Returns:
            Lista ścieżek do plików muzycznych
        """
        music_files = []
        
        try:
            if recursive:
                for file_path in directory.rglob('*'):
                    if file_path.is_file() and self._is_supported_format(file_path):
                        music_files.append(file_path)
            else:
                for file_path in directory.iterdir():
                    if file_path.is_file() and self._is_supported_format(file_path):
                        music_files.append(file_path)
                        
        except Exception as e:
            logger.error(f"Błąd podczas skanowania katalogu {directory}: {e}")
            
        logger.info(f"Znaleziono {len(music_files)} plików muzycznych w {directory}")
        return music_files
    
    def analyze_batch(self, file_paths: List[Path]) -> List[Dict]:
        """
        Analizuje wiele plików naraz
        
        Args:
            file_paths: Lista ścieżek do plików
            
        Returns:
            Lista słowników z metadanymi
        """
        results = []
        
        for i, file_path in enumerate(file_paths, 1):
            logger.info(f"Analizowanie {i}/{len(file_paths)}: {file_path.name}")
            metadata = self.extract_metadata(file_path)
            results.append(metadata)
            
        return results

# Funkcje pomocnicze
def format_duration(seconds: float) -> str:
    """Formatuje czas trwania w sekundach na format MM:SS"""
    if not seconds:
        return "00:00"
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes: int) -> str:
    """Formatuje rozmiar pliku w bajtach na czytelny format"""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
        
    return f"{size:.1f} {units[unit_index]}"