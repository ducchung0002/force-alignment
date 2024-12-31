from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import os
import subprocess
import json
import sys

app = Flask(__name__)

# Ensure the folder for uploads exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set up the upload folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'wav', 'mp3', 'ogg', 'flac'}

cors_config = {
    "origins": "*",
    "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["X-Total-Count", "X-Page", "X-Per-Page"],
    "credentials": True
}
CORS(app, resources={r"/*": cors_config})

# Helper function to check if the file has an allowed extension


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@app.route('/align', methods=['POST'])
def align():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    if 'lyric' not in request.form:
        return jsonify({'error': 'No lyric provided'}), 400
    if 'start_time' not in request.form:
        return jsonify({'error': 'No start time provided'}), 400

    file = request.files['file']
    lyric = request.form['lyric']
    start_time = request.form['start_time']
    

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Save the file
        unique_name = uuid.uuid4().hex
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name + '.wav')
        file.save(audio_path)
        
        lyric_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name + '.txt')
        with open(lyric_path, 'w', encoding='utf-8', newline='\n') as file:
            file.write('\n'.join(line.strip() for line in lyric.splitlines() if line.strip()))

        lyric_align_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name + '.json')
        command = [
            sys.executable, # Uses the Python interpreter running the current script
            "inference.py",
            "--audio", audio_path,
            "--lyric", lyric_path,
            "--start", str(start_time),
            "--out", lyric_align_path
        ]

        subprocess.run(command, check=True)
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
        if os.path.exists(lyric_path):
            os.remove(lyric_path)
        
        with open(lyric_align_path, "r", encoding="utf-8") as file:
            lyric_align = json.load(file)
        
        if os.path.exists(lyric_align_path):
            os.remove(lyric_align_path)
        
        return jsonify(lyric_align), 200
        
    else:
        return jsonify({'error': 'Invalid file format'}), 400


if __name__ == '__main__':
    from gevent.pywsgi import WSGIServer
    server = WSGIServer(('0.0.0.0', 6666), app)
    print("Server running on http://0.0.0.0:6666")
    server.serve_forever()
