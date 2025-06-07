import os
import shutil
from flask import Flask, render_template, request, jsonify

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

@app.route('/')
def index():
    files = [f for f in os.listdir(DOWNLOADS_DIR) if is_eligible_file(f)]
    show_folders = sorted([
        name for name in os.listdir(SERIES_DIR)
        if os.path.isdir(os.path.join(SERIES_DIR, name))
    ])
    return render_template('index.html', files=files, shows=show_folders)

@app.route('/move', methods=['POST'])
def move_file():
    data = request.json
    filename = data['filename']
    media_type = data['mediaType']
    show_name = data.get('showName')
    overwrite = data.get('overwrite', False)

    src = os.path.join(DOWNLOADS_DIR, filename)

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
    app.run(host='0.0.0.0', port=8080)
