# Music Genre Sorter (GUI)

A Windows-friendly GUI app to classify and organize your music library by genre. It uses metadata, local heuristics, and AI analysis to infer genres, confidence, tags, BPM, and remix information, then builds a clean folder structure and can rename files to the "Artist – Title (Year)" format.

## Key Features
- Combined signals: metadata + filename hints + AI reasoning.
- Fields: `primary_genre`, `secondary_genre`, `confidence_score`, tags, BPM, `is_remix`, `remix_style`.
- Confidence-aware sorting: low-confidence → `Needs Review`.
- Pretty filenames: sanitized and unique "Artist – Title (Year).ext".
- Copy vs move: copy by default; optionally move originals.
- CSV export/import: reuse analysis; avoid re-running AI on large sets.
- Reports: JSON operation log, textual summary; per-folder counts.
- Optional M3U playlist generation per genre.

## Requirements
- Windows
- Python 3.11+
- `pip install -r requirements.txt`

## Quick Start
```powershell
# In project root
pip install -r requirements.txt
python main.py
```
Alternatively use `uruchom_music_sorter.bat`.

## Usage
- Choose source directory with music files and output directory.
- Click "Skanuj" to list files, then "Analizuj" to classify.
- Review results (genre, confidence, folder) and AI reasoning.
- Click "Sortuj pliki" to organize: copy/move into genre folders.

### Copy vs Move
- Default is copy (originals stay in place).
- To move instead, uncheck "Kopiuj pliki (zamiast przenosić oryginały)" in Settings.

### CSV Import/Export
- Export: "Eksportuj do CSV" → `File, Artist, Title, Genre, Confidence, Folder`.
- Import: "Importuj z CSV" → rebuilds classifications without re-analysis.

### Reports
- Sorting report dialog shows: total, processed, moved, copied, skipped, errors, test mode.
- JSON logs: `output/reports/organization_report_YYYYMMDD_HHMMSS.json`.
- Text summary: "Zapisz raport".

## Project Structure
- `main.py` – entry point
- `gui.py` – Tkinter GUI
- `metadata_analyzer.py` – metadata scanning
- `web_searcher.py` – AI calls + fallback BPM/remix parsing
- `genre_classifier.py` – classification & stats
- `file_organizer.py` – copy/move, pretty names, reports, playlists
- `config.py` – configuration & genre folder names
- `requirements.txt` – dependencies

## Troubleshooting
- No files moved: copying is default; uncheck to move.
- AI fields missing: fallback parser extracts BPM/remix hints from text.
- Ensure OpenAI API key is set in GUI or environment.

## License
MIT (recommended). Add a `LICENSE` file if you prefer explicit licensing.