"""
Moduł do organizacji i sortowania plików muzycznych
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

from config import DEFAULT_OUTPUT_DIR

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileOrganizer:
    """Klasa do organizacji plików muzycznych według gatunków"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.operation_log = []
        self.dry_run = False
        
    def organize_files(self, classifications: List[Dict], dry_run: bool = False, use_pretty_names: bool = True, force_copy: bool = False) -> Dict:
        """
        Organizuje pliki według klasyfikacji gatunków
        
        Args:
            classifications: Lista klasyfikacji utworów
            dry_run: Czy tylko symulować operacje
            
        Returns:
            Raport z operacji
        """
        self.dry_run = dry_run
        self.operation_log = []
        
        report = {
            'total_files': len(classifications),
            'processed_files': 0,
            'moved_files': 0,
            'copied_files': 0,
            'skipped_files': 0,
            'errors': 0,
            'operations': [],
            'folder_structure': {},
            'dry_run': dry_run
        }
        
        # Tworzenie struktury folderów
        if not dry_run:
            self._create_folder_structure(classifications)
        
        # Przetwarzanie każdego pliku
        for classification in classifications:
            try:
                result = self._process_single_file(classification, dry_run, use_pretty_names, force_copy)
                report['operations'].append(result)
                
                if result['status'] == 'moved':
                    report['moved_files'] += 1
                elif result['status'] == 'copied':
                    report['copied_files'] += 1
                elif result['status'] == 'skipped':
                    report['skipped_files'] += 1
                    
                report['processed_files'] += 1
                
            except Exception as e:
                error_msg = f"Błąd podczas przetwarzania {classification.get('file_path', 'unknown')}: {e}"
                logger.error(error_msg)
                report['errors'] += 1
                report['operations'].append({
                    'file_path': classification.get('file_path', 'unknown'),
                    'status': 'error',
                    'error': str(e)
                })
        
        # Generowanie struktury folderów
        report['folder_structure'] = self._get_folder_structure()
        
        # Zapisanie raportu
        self._save_report(report)
        
        return report
    
    def _process_single_file(self, classification: Dict, dry_run: bool = False, use_pretty_names: bool = True, force_copy: bool = False) -> Dict:
        """Przetwarza pojedynczy plik"""
        source_path = Path(classification.get('file_path', ''))
        
        if not source_path.exists():
            return {
                'file_path': str(source_path),
                'status': 'error',
                'error': 'Plik nie istnieje'
            }
        
        # Określenie folderu docelowego
        target_folder = classification.get('suggested_folder', 'Other')
        confidence = classification.get('confidence_score', 0)
        
        # Jeśli niska pewność, umieść w folderze "Needs Review"
        if confidence < 0.5 and target_folder != 'Unsorted':
            target_folder = 'Needs Review'
        
        # Generowanie ładnej nazwy pliku
        pretty_filename = self._generate_pretty_filename(classification, source_path, use_pretty_names)
        
        # Ścieżka docelowa
        target_dir = self.output_dir / target_folder
        target_path = target_dir / pretty_filename
        
        # Sprawdzenie czy plik już istnieje
        if target_path.exists():
            target_path = self._get_unique_filename(target_path)
        
        operation = {
            'source_path': str(source_path),
            'target_path': str(target_path),
            'target_folder': target_folder,
            'confidence': confidence,
            'primary_genre': classification.get('primary_genre', 'unknown'),
            'status': 'planned'
        }
        
        # Wykonanie operacji (jeśli nie dry run)
        if not dry_run:
            try:
                # Tworzenie katalogu docelowego
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # Kopiowanie lub przenoszenie pliku
                if force_copy or self._should_copy_file(source_path, target_path):
                    shutil.copy2(source_path, target_path)
                    operation['status'] = 'copied'
                    operation['action'] = 'copy'
                    logger.info(f"Skopiowano: {source_path.name} -> {target_folder}")
                else:
                    shutil.move(str(source_path), str(target_path))
                    operation['status'] = 'moved'
                    operation['action'] = 'move'
                    logger.info(f"Przeniesiono: {source_path.name} -> {target_folder}")
            except Exception as e:
                operation['status'] = 'error'
                operation['error'] = str(e)
                logger.error(f"Błąd podczas przenoszenia {source_path}: {e}")
        else:
            operation['status'] = 'simulated'
            operation['action'] = 'move'
        
        self.operation_log.append(operation)
        return operation
    
    def _generate_pretty_filename(self, classification: Dict, original_path: Path, use_pretty_names: bool = True) -> str:
        """
        Generuje ładną nazwę pliku w formacie: Wykonawca - Tytuł (Rok).ext
        
        Args:
            classification: Słownik z klasyfikacją i metadanymi
            original_path: Oryginalna ścieżka pliku
            
        Returns:
            Ładna nazwa pliku
        """
        try:
            # Jeśli ładne nazwy są wyłączone, użyj oryginalnej nazwy
            if not use_pretty_names:
                return original_path.name
            
            metadata = classification.get('metadata', {})
            
            # Pobranie metadanych
            artist = metadata.get('artist', '').strip()
            title = metadata.get('title', '').strip()
            year = metadata.get('year', '').strip()
            
            # Jeśli brak artysty lub tytułu, użyj oryginalnej nazwy
            if not artist or not title:
                logger.warning(f"Brak artysty lub tytułu dla {original_path.name} - używam oryginalnej nazwy")
                return original_path.name
            
            # Oczyszczenie nazw z niedozwolonych znaków
            artist = self._clean_filename_part(artist)
            title = self._clean_filename_part(title)
            
            # Budowanie nazwy pliku
            if year and year.isdigit():
                filename = f"{artist} - {title} ({year})"
            else:
                filename = f"{artist} - {title}"
            
            # Dodanie rozszerzenia
            filename += original_path.suffix
            
            # Ograniczenie długości nazwy pliku (Windows ma limit 255 znaków)
            if len(filename) > 200:
                # Skrócenie tytułu jeśli nazwa jest za długa
                max_title_length = 200 - len(artist) - len(year) - 10  # 10 na " - " + " ()" + rozszerzenie
                title = title[:max_title_length] + "..."
                if year and year.isdigit():
                    filename = f"{artist} - {title} ({year}){original_path.suffix}"
                else:
                    filename = f"{artist} - {title}{original_path.suffix}"
            
            logger.info(f"Wygenerowano ładną nazwę: {original_path.name} -> {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania ładnej nazwy dla {original_path.name}: {e}")
            return original_path.name
    
    def _clean_filename_part(self, text: str) -> str:
        """
        Oczyszcza część nazwy pliku z niedozwolonych znaków
        
        Args:
            text: Tekst do oczyszczenia
            
        Returns:
            Oczyszczony tekst
        """
        # Znaki niedozwolone w nazwach plików Windows
        forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        for char in forbidden_chars:
            text = text.replace(char, '')
        
        # Usunięcie wielokrotnych spacji i spacji na początku/końcu
        text = ' '.join(text.split())
        
        return text
    
    def _should_copy_file(self, source_path: Path, target_path: Path) -> bool:
        """Określa czy plik powinien być skopiowany czy przeniesiony"""
        # Kopiuj jeśli źródło i cel są na różnych dyskach
        try:
            return source_path.stat().st_dev != target_path.parent.stat().st_dev
        except:
            return False
    
    def _get_unique_filename(self, file_path: Path) -> Path:
        """Generuje unikalną nazwę pliku jeśli plik już istnieje"""
        base = file_path.stem
        extension = file_path.suffix
        directory = file_path.parent
        counter = 1
        
        while file_path.exists():
            new_name = f"{base}_{counter}{extension}"
            file_path = directory / new_name
            counter += 1
            
        return file_path
    
    def _create_folder_structure(self, classifications: List[Dict]):
        """Tworzy strukturę folderów na podstawie klasyfikacji"""
        folders_to_create = set()
        
        for classification in classifications:
            folder = classification.get('suggested_folder', 'Other')
            confidence = classification.get('confidence_score', 0)
            
            if confidence < 0.5 and folder != 'Unsorted':
                folder = 'Needs Review'
                
            folders_to_create.add(folder)
        
        # Dodanie standardowych folderów
        folders_to_create.update(['Needs Review', 'Duplicates', 'Unsupported', 'Unsorted'])
        
        # Tworzenie folderów
        for folder in folders_to_create:
            folder_path = self.output_dir / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Utworzono folder: {folder_path}")
    
    def _get_folder_structure(self) -> Dict:
        """Zwraca strukturę folderów z liczbą plików"""
        structure = {}
        
        if not self.output_dir.exists():
            return structure
            
        for item in self.output_dir.iterdir():
            if item.is_dir():
                file_count = len([f for f in item.iterdir() if f.is_file()])
                structure[item.name] = {
                    'file_count': file_count,
                    'path': str(item)
                }
        
        return structure
    
    def _save_report(self, report: Dict):
        """Zapisuje raport operacji"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"organization_report_{timestamp}.json"
        report_path = self.output_dir / "reports" / report_filename
        
        # Tworzenie katalogu raportów
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Zapisano raport: {report_path}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania raportu: {e}")
    
    def create_playlist_files(self, classifications: List[Dict]):
        """Tworzy pliki playlist dla każdego gatunku"""
        playlists = {}
        
        for classification in classifications:
            genre = classification.get('primary_genre', 'unknown')
            file_path = classification.get('file_path', '')
            
            if genre not in playlists:
                playlists[genre] = []
            
            playlists[genre].append(file_path)
        
        # Tworzenie plików M3U
        playlist_dir = self.output_dir / "playlists"
        playlist_dir.mkdir(parents=True, exist_ok=True)
        
        for genre, files in playlists.items():
            if files:
                playlist_path = playlist_dir / f"{genre}.m3u"
                try:
                    with open(playlist_path, 'w', encoding='utf-8') as f:
                        f.write("#EXTM3U\\n")
                        for file_path in files:
                            f.write(f"{file_path}\\n")
                    logger.info(f"Utworzono playlistę: {playlist_path}")
                except Exception as e:
                    logger.error(f"Błąd podczas tworzenia playlisty {genre}: {e}")
    
    def cleanup_empty_folders(self, root_dir: Path = None):
        """Usuwa puste foldery"""
        if root_dir is None:
            root_dir = self.output_dir
            
        removed_folders = []
        
        for folder_path in root_dir.rglob('*'):
            if folder_path.is_dir():
                try:
                    # Sprawdź czy folder jest pusty
                    if not any(folder_path.iterdir()):
                        folder_path.rmdir()
                        removed_folders.append(str(folder_path))
                        logger.info(f"Usunięto pusty folder: {folder_path}")
                except OSError:
                    pass  # Folder nie jest pusty lub nie można go usunąć
        
        return removed_folders
    
    def generate_summary_report(self, classifications: List[Dict]) -> str:
        """Generuje tekstowy raport podsumowujący"""
        if not classifications:
            return "Brak danych do analizy."
        
        # Statystyki gatunków
        genre_stats = {}
        confidence_stats = {'high': 0, 'medium': 0, 'low': 0}
        
        for classification in classifications:
            genre = classification.get('primary_genre', 'unknown')
            confidence = classification.get('confidence_score', 0)
            
            genre_stats[genre] = genre_stats.get(genre, 0) + 1
            
            if confidence > 0.7:
                confidence_stats['high'] += 1
            elif confidence > 0.4:
                confidence_stats['medium'] += 1
            else:
                confidence_stats['low'] += 1
        
        # Generowanie raportu
        report_lines = [
            "=== RAPORT SORTOWANIA MUZYKI ===",
            f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Łączna liczba plików: {len(classifications)}",
            "",
            "ROZKŁAD GATUNKÓW:",
        ]
        
        for genre, count in sorted(genre_stats.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(classifications)) * 100
            report_lines.append(f"  {genre}: {count} plików ({percentage:.1f}%)")
        
        report_lines.extend([
            "",
            "POZIOM PEWNOŚCI KLASYFIKACJI:",
            f"  Wysoki (>70%): {confidence_stats['high']} plików",
            f"  Średni (40-70%): {confidence_stats['medium']} plików", 
            f"  Niski (<40%): {confidence_stats['low']} plików",
            "",
            f"Pliki wymagające przeglądu: {confidence_stats['low']}",
            "",
            "=== KONIEC RAPORTU ==="
        ])
        
        return "\\n".join(report_lines)
    
    def backup_original_structure(self, source_dir: Path):
        """Tworzy kopię zapasową oryginalnej struktury folderów"""
        backup_dir = self.output_dir / "backup" / "original_structure"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        structure_file = backup_dir / "folder_structure.txt"
        
        try:
            with open(structure_file, 'w', encoding='utf-8') as f:
                f.write(f"Oryginalna struktura folderów z: {source_dir}\\n")
                f.write(f"Data utworzenia kopii: {datetime.now()}\\n\\n")
                
                for root, dirs, files in os.walk(source_dir):
                    level = root.replace(str(source_dir), '').count(os.sep)
                    indent = ' ' * 2 * level
                    f.write(f"{indent}{os.path.basename(root)}/\\n")
                    
                    subindent = ' ' * 2 * (level + 1)
                    for file in files:
                        f.write(f"{subindent}{file}\\n")
            
            logger.info(f"Zapisano kopię struktury folderów: {structure_file}")
            
        except Exception as e:
            logger.error(f"Błąd podczas tworzenia kopii struktury: {e}")