"""
Simple Face Swap Video App
A personal-use web app for creating fun videos by overlaying faces on templates
Optimized for mobile (iPhone) use
"""

from flask import Flask, render_template, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename
import cv2
import mediapipe as mp
import numpy as np
import os
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['TEMPLATE_FOLDER'] = 'static/template_videos'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_and_extract_face(image_path):
    """
    Detect face in image and extract it with padding
    Returns: face image (numpy array) or None if no face found
    """
    mp_face_detection = mp.solutions.face_detection

    # Read image
    image = cv2.imread(image_path)
    if image is None:
        return None

    # Convert to RGB for MediaPipe
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect faces
    with mp_face_detection.FaceDetection(
        model_selection=1,  # 1 for full range, 0 for short range
        min_detection_confidence=0.5
    ) as face_detection:
        results = face_detection.process(image_rgb)

        if not results.detections:
            return None

        # Get first detected face
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box

        # Convert relative coordinates to absolute
        h, w = image.shape[:2]
        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)

        # Add padding (20%)
        padding = int(min(width, height) * 0.2)
        x = max(0, x - padding)
        y = max(0, y - padding)
        width = min(w - x, width + 2 * padding)
        height = min(h - y, height + 2 * padding)

        # Extract face
        face = image[y:y+height, x:x+width]

        return face

def create_face_overlay_video(template_name, face_image_path, output_path):
    """
    Create video with face overlaid on template
    Uses FFmpeg for video processing
    """
    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.mp4')

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template {template_name} not found")

    # Extract face
    face = detect_and_extract_face(face_image_path)
    if face is None:
        raise ValueError("No face detected in image")

    # Save face as temporary PNG with transparency
    face_temp = f"temp/face_{uuid.uuid4().hex}.png"
    cv2.imwrite(face_temp, face)

    try:
        # Get template video info
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            template_path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        video_width, video_height = map(int, result.stdout.strip().split('x'))

        # Calculate face size (proportional to video size)
        face_size = int(min(video_width, video_height) * 0.25)  # 25% of video size

        # Calculate position (center-top area where faces usually are)
        x_pos = int(video_width * 0.5 - face_size * 0.5)  # Center horizontally
        y_pos = int(video_height * 0.15)  # Top 15% of frame

        # FFmpeg command to overlay face
        ffmpeg_cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-i', template_path,  # Input video
            '-i', face_temp,  # Input face image
            '-filter_complex',
            f'[1:v]scale={face_size}:{face_size}[face];'  # Scale face
            f'[0:v][face]overlay={x_pos}:{y_pos}',  # Overlay on video
            '-c:a', 'copy',  # Copy audio
            '-c:v', 'libx264',  # H.264 video codec
            '-preset', 'fast',  # Fast encoding
            '-crf', '23',  # Quality (lower = better, 23 is good)
            output_path
        ]

        # Run FFmpeg
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)

    finally:
        # Clean up temporary face file
        if os.path.exists(face_temp):
            os.remove(face_temp)

    return output_path

@app.route('/')
def index():
    """Main page"""
    # Get available templates
    templates = []
    template_dir = Path(app.config['TEMPLATE_FOLDER'])

    if template_dir.exists():
        for template_file in template_dir.glob('*.mp4'):
            template_name = template_file.stem
            templates.append({
                'id': template_name,
                'name': template_name.replace('_', ' ').title(),
                'url': url_for('static', filename=f'template_videos/{template_file.name}')
            })

    return render_template('index.html', templates=templates)

@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handle photo upload and face detection"""
    if 'photo' not in request.files:
        return jsonify({'success': False, 'error': 'No photo uploaded'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Use JPG or PNG'}), 400

    # Save uploaded file
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check for face
    face = detect_and_extract_face(filepath)
    if face is None:
        os.remove(filepath)  # Clean up
        return jsonify({'success': False, 'error': 'No face detected. Please use a clear photo with a visible face.'}), 400

    return jsonify({
        'success': True,
        'filename': filename,
        'message': 'Face detected successfully!'
    })

@app.route('/generate', methods=['POST'])
def generate_video():
    """Generate video with face overlay"""
    data = request.get_json()

    if not data or 'filename' not in data or 'template' not in data:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

    filename = data['filename']
    template = data['template']

    # Validate inputs
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Uploaded photo not found'}), 404

    # Generate output filename
    output_filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        # Create video
        create_face_overlay_video(template, filepath, output_path)

        # Clean up uploaded photo (optional - comment out if you want to keep uploads)
        # os.remove(filepath)

        return jsonify({
            'success': True,
            'video_url': url_for('static', filename=f'output/{output_filename}'),
            'download_url': url_for('download_video', filename=output_filename)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_video(filename):
    """Download generated video"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if not os.path.exists(filepath):
        return "File not found", 404

    return send_file(filepath, as_attachment=True, download_name=f"face_swap_{filename}")

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMPLATE_FOLDER'], exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # Run app
    # For iPhone access on same WiFi, use host='0.0.0.0'
    app.run(host='0.0.0.0', port=5000, debug=True)
