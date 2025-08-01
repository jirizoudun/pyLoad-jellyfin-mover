import os
import shutil
import threading
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
import logging

logging.basicConfig(
    level=logging.INFO,  # or DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

DOWNLOADS_DIR = os.environ.get('DOWNLOADS_DIR', '/app/Downloads')
MOVIES_DIR = os.environ.get('MOVIES_DIR', '/app/Movies')
SERIES_DIR = os.environ.get('SERIES_DIR', '/app/Series')
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
SUBTITLE_EXTENSIONS = ['.srt', '.sub']
INCOMPLETE_SUFFIXES = ['.part', '.tmp']

# Global progress tracking storage
file_operations = {}
operations_lock = threading.Lock()

def set_file_status(filename, status, progress=0, message=""):
    """Update file operation status"""
    with operations_lock:
        file_operations[filename] = {
            'status': status,  # pending, in_progress, completed, failed
            'progress': progress,  # 0-100
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    logging.info(f"Status updated for {filename}: {status} ({progress}%) - {message}")

def get_file_status(filename):
    """Get file operation status"""
    with operations_lock:
        return file_operations.get(filename, {
            'status': 'pending',
            'progress': 0,
            'message': '',
            'timestamp': None
        })

def cleanup_old_operations():
    """Remove completed/failed operations older than 1 hour"""
    cutoff_time = datetime.now().timestamp() - 3600  # 1 hour ago
    with operations_lock:
        to_remove = []
        for filename, data in file_operations.items():
            if data['status'] in ['completed', 'failed'] and data['timestamp']:
                op_time = datetime.fromisoformat(data['timestamp']).timestamp()
                if op_time < cutoff_time:
                    to_remove.append(filename)
        for filename in to_remove:
            del file_operations[filename]
            logging.info(f"Cleaned up old operation: {filename}")

def is_eligible_file(filename):
    ext = os.path.splitext(filename)[1].lower()
    if any(filename.endswith(sfx) for sfx in INCOMPLETE_SUFFIXES):
        return False
    return ext in VIDEO_EXTENSIONS + SUBTITLE_EXTENSIONS

def get_all_files():
    eligible_files = []
    for root, dirs, files in os.walk(DOWNLOADS_DIR):
        logging.info(f"Found {len(files)} files in {root}")
        for file in files:
            if is_eligible_file(file):
                # Store as a relative path from DOWNLOADS_DIR
                rel_path = os.path.relpath(os.path.join(root, file), DOWNLOADS_DIR)
                eligible_files.append(rel_path)
    logging.info(f"Found {len(eligible_files)} eligible files")
    return eligible_files

def move_file_with_progress(src, dst, filename, overwrite=False):
    """Move file with progress tracking"""
    try:
        set_file_status(filename, 'in_progress', 0, 'Starting file move...')
        
        # Check if destination exists
        if os.path.exists(dst):
            if not overwrite:
                set_file_status(filename, 'failed', 0, 'File exists at destination')
                return {'status': 'conflict', 'message': 'File exists at destination'}
            else:
                os.remove(dst)
                set_file_status(filename, 'in_progress', 10, 'Removed existing file...')
        
        # Get file size for progress calculation
        file_size = os.path.getsize(src)
        set_file_status(filename, 'in_progress', 20, f'Moving {file_size} bytes...')
        
        # For small files, just move directly
        if file_size < 10 * 1024 * 1024:  # Less than 10MB
            set_file_status(filename, 'in_progress', 50, 'Moving file...')
            shutil.move(src, dst)
            set_file_status(filename, 'completed', 100, 'File moved successfully')
            return {'status': 'ok'}
        
        # For larger files, copy with progress
        set_file_status(filename, 'in_progress', 30, 'Copying file with progress...')
        
        with open(src, 'rb') as fsrc:
            with open(dst, 'wb') as fdst:
                copied = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                while True:
                    chunk = fsrc.read(chunk_size)
                    if not chunk:
                        break
                    
                    fdst.write(chunk)
                    copied += len(chunk)
                    
                    # Update progress (30% to 90% for copying)
                    progress = 30 + int((copied / file_size) * 60)
                    set_file_status(filename, 'in_progress', progress, f'Copied {copied}/{file_size} bytes')
                    
                    # Small delay to make progress visible for testing
                    time.sleep(0.1)
        
        # Remove source file
        set_file_status(filename, 'in_progress', 95, 'Removing source file...')
        os.remove(src)
        
        set_file_status(filename, 'completed', 100, 'File moved successfully')
        return {'status': 'ok'}
        
    except Exception as e:
        error_msg = f'Error moving file: {str(e)}'
        set_file_status(filename, 'failed', 0, error_msg)
        logging.error(f"File move failed for {filename}: {e}")
        return {'status': 'error', 'message': error_msg}

@app.route('/')
def index():
    logging.info(f"Getting all files")
    files = get_all_files()
    show_folders = sorted([
        name for name in os.listdir(SERIES_DIR)
        if os.path.isdir(os.path.join(SERIES_DIR, name))
    ])
    logging.info(f"Found {len(show_folders)} show folders")
    return render_template('index.html', files=files, shows=show_folders)

@app.route('/move', methods=['POST'])
def move_file():
    data = request.json
    rel_path = data['filename']  # This is now a relative path
    media_type = data['mediaType']
    show_name = data.get('showName')
    overwrite = data.get('overwrite', False)

    src = os.path.join(DOWNLOADS_DIR, rel_path)
    filename = os.path.basename(rel_path)

    # Validate source file exists
    if not os.path.exists(src):
        return jsonify({'status': 'error', 'message': 'Source file not found'}), 404

    if media_type == 'movie':
        dst_dir = MOVIES_DIR
    elif media_type == 'tvshow':
        if not show_name:
            return jsonify({'status': 'error', 'message': 'Show name required for TV shows'}), 400
        dst_dir = os.path.join(SERIES_DIR, show_name)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
    else:
        return jsonify({'status': 'error', 'message': 'Invalid media type'}), 400

    dst = os.path.join(dst_dir, filename)

    # Check if operation is already in progress
    current_status = get_file_status(filename)
    if current_status['status'] == 'in_progress':
        return jsonify({'status': 'error', 'message': 'File move already in progress'}), 409

    # Start file move in background thread
    def move_thread():
        move_file_with_progress(src, dst, filename, overwrite)
    
    thread = threading.Thread(target=move_thread)
    thread.daemon = True
    thread.start()
    
    # Return immediately - client will poll for status
    return jsonify({'status': 'started', 'message': 'File move started'})

@app.route('/shows', methods=['GET'])
def get_shows():
    show_folders = sorted([
        name for name in os.listdir(SERIES_DIR)
        if os.path.isdir(os.path.join(SERIES_DIR, name))
    ])
    return jsonify(show_folders)

@app.route('/status', methods=['GET'])
def get_all_status():
    """Get status of all file operations"""
    cleanup_old_operations()  # Clean up old operations
    with operations_lock:
        return jsonify(dict(file_operations))

@app.route('/status/<path:filename>', methods=['GET'])
def get_file_status_api(filename):
    """Get status of specific file operation"""
    status = get_file_status(filename)
    return jsonify(status)

@app.route('/move-batch', methods=['POST'])
def move_files_batch():
    """Move multiple files in batch"""
    data = request.json
    files = data.get('files', [])
    
    if not files:
        return jsonify({'status': 'error', 'message': 'No files provided'}), 400
    
    started_count = 0
    errors = []
    
    for file_data in files:
        try:
            rel_path = file_data['filename']
            media_type = file_data['mediaType']
            show_name = file_data.get('showName')
            overwrite = file_data.get('overwrite', False)
            
            
            src = os.path.join(DOWNLOADS_DIR, rel_path)
            filename = os.path.basename(rel_path)
            
            # Validate source file exists
            if not os.path.exists(src):
                errors.append(f'{filename}: Source file not found')
                continue
            
            # Check if already in progress
            current_status = get_file_status(filename)
            if current_status['status'] == 'in_progress':
                errors.append(f'{filename}: Already in progress')
                continue
                
            # Determine destination directory
            if media_type == 'movie':
                dst_dir = MOVIES_DIR
            elif media_type == 'tvshow':
                if not show_name:
                    errors.append(f'{filename}: Show name required for TV shows')
                    continue
                dst_dir = os.path.join(SERIES_DIR, show_name)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir, exist_ok=True)
            else:
                errors.append(f'{filename}: Invalid media type')
                continue
            
            dst = os.path.join(dst_dir, filename)
            
            # Start file move in background thread
            def move_thread(src_path, dst_path, file_name, overwrite_flag):
                move_file_with_progress(src_path, dst_path, file_name, overwrite_flag)
            
            thread = threading.Thread(target=move_thread, args=(src, dst, filename, overwrite))
            thread.daemon = True
            thread.start()
            
            started_count += 1
            
        except Exception as e:
            errors.append(f'{filename}: {str(e)}')
    
    response = {
        'status': 'batch_started',
        'started_count': started_count,
        'total_count': len(files)
    }
    
    if errors:
        response['errors'] = errors
    
    return jsonify(response)

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("FLASK_PORT", "8080"))
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
