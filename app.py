import os
import shutil
from flask import Flask, render_template, request, jsonify
import logging

logging.basicConfig(
    level=logging.INFO,  # or DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = Flask(__name__)

DOWNLOADS_DIR = '/app/Downloads'
MOVIES_DIR = '/app/Movies'
SERIES_DIR = '/app/Series'
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
SUBTITLE_EXTENSIONS = ['.srt', '.sub']
INCOMPLETE_SUFFIXES = ['.part', '.tmp']

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

    if media_type == 'movie':
        dst_dir = MOVIES_DIR
    elif media_type == 'tvshow':
        dst_dir = os.path.join(SERIES_DIR, show_name)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir, exist_ok=True)
    else:
        return jsonify({'status': 'error', 'message': 'Invalid media type'}), 400

    dst = os.path.join(dst_dir, filename)

    if os.path.exists(dst):
        if not overwrite:
            return jsonify({'status': 'conflict', 'message': 'File exists at destination'})
        else:
            os.remove(dst)

    try:
        shutil.move(src, dst)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/shows', methods=['GET'])
def get_shows():
    show_folders = sorted([
        name for name in os.listdir(SERIES_DIR)
        if os.path.isdir(os.path.join(SERIES_DIR, name))
    ])
    return jsonify(show_folders)

if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host='0.0.0.0', port=8080, debug=debug_mode)
