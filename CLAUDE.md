# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based web application that provides a user interface for moving downloaded media files from a pyLoad downloads directory to organized directories for Movies and TV Series (compatible with Jellyfin media server structure).

## Architecture

### Core Components

- **app.py**: Main Flask application with three key routes:
  - `/` - Dashboard showing all eligible files from downloads directory
  - `/move` - POST endpoint to move files to Movies or Series directories
  - `/shows` - GET endpoint returning available TV show folders

- **templates/index.html**: Single-page web interface using Tailwind CSS with JavaScript for file movement operations

### Key Functions

**Backend (app.py):**
- `get_all_files()` (app.py:68): Recursively scans downloads directory for eligible media files
- `is_eligible_file()` (app.py:62): Filters files by extension and excludes incomplete downloads
- `set_file_status()` (app.py:27): Thread-safe progress tracking storage
- `get_file_status()` (app.py:38): Retrieve file operation status
- `move_file_with_progress()` (app.py:80): Chunked file copying with progress updates
- `/move` endpoint (app.py:152): Threaded file operations returning immediately
- `/status` endpoints (app.py:133): Real-time progress tracking API

**Frontend (index.html):**
- `updateFileStatus()` (index.html:132): Updates progress bars and status display
- `pollStatus()` (index.html:179): Polls server every 2 seconds for status updates
- `moveFile()` (index.html:200): Initiates file move operations

### Directory Structure

The application expects these Docker volume mounts:
- `/app/Downloads` - Source directory for downloaded files
- `/app/Movies` - Destination for movie files
- `/app/Series` - Destination for TV show files (creates subdirectories per show)

### File Handling

- Supported video formats: .mp4, .mkv, .avi, .mov, .wmv
- Supported subtitle formats: .srt, .sub
- Excludes incomplete files with .part or .tmp suffixes
- Handles file conflicts with overwrite confirmation

## Development Commands

### Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set up test environment with configurable paths
export DOWNLOADS_DIR="./test/Downloads"
export MOVIES_DIR="./test/Movies" 
export SERIES_DIR="./test/Series"
export FLASK_DEBUG=1
export FLASK_PORT=9000  # Use different port to avoid conflicts

# Create test directories and sample files
mkdir -p test/{Downloads,Movies,Series}
touch test/Downloads/{video1.mp4,video2.mkv,episode_s01e01.mp4,show_s02e04.mp4}

# Run in development mode
python app.py
```

### Docker Development
```bash
# Build image
docker build -t pyload-jellyfin-mover .

# Run with docker-compose (uses port 8080)
docker-compose up -d

# View logs
docker-compose logs -f
```

### Testing Progress Tracking
```bash
# Create larger test file for progress testing
dd if=/dev/zero of=test/Downloads/big_movie.mp4 bs=1024 count=100000

# Reset test state (move files back to Downloads)
rm -f test/Movies/* test/Series/*/*
```

### API Testing
```bash
# Check file status
curl "http://localhost:9000/status"
curl "http://localhost:9000/status/filename.mp4"

# Test file move
curl -X POST "http://localhost:9000/move" \
  -H "Content-Type: application/json" \
  -d '{"filename": "video1.mp4", "mediaType": "movie"}'
```

## Progress Tracking System

### Implementation Details
- **In-memory storage**: Thread-safe dictionary `file_operations` with status, progress, message, timestamp
- **Status polling**: Frontend polls `/status` endpoint every 2 seconds
- **Progress calculation**: Chunked file copying with percentage updates (0-100%)
- **Threading**: Background operations using `threading.Thread` for non-blocking moves
- **Persistence**: Status survives browser refreshes until cleanup (1 hour for completed/failed)

### Status States
- `pending`: File not yet processed
- `in_progress`: File move operation running with progress updates
- `completed`: File successfully moved (green progress bar)
- `failed`: Error occurred (red progress bar with error message)

### Testing Notes
- Files <10MB: Instant move with progress jumps
- Files >10MB: Chunked copying with real-time progress updates
- Use `dd` to create large test files for progress testing
- Progress persists across browser refreshes

## Environment Variables

- `FLASK_DEBUG`: Set to "1" to enable Flask debug mode
- `FLASK_ENV`: Set to "production" for production deployment (used in docker-compose)
- `FLASK_PORT`: Port number (default: 8080, use 9000 for local dev)
- `DOWNLOADS_DIR`: Source directory path (default: `/app/Downloads`)
- `MOVIES_DIR`: Movies destination path (default: `/app/Movies`)
- `SERIES_DIR`: TV series destination path (default: `/app/Series`)

## File Paths

**Containerized (Docker):**
- Downloads source: `/app/Downloads` (mapped to `~/Downloads`)
- Movies destination: `/app/Movies` (mapped to `~/Movies`) 
- Series destination: `/app/Series` (mapped to `~/Series`)

**Local Development:**
- Downloads source: `./test/Downloads`
- Movies destination: `./test/Movies`
- Series destination: `./test/Series`