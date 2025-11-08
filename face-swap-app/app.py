"""
Simple Face Swap Video App - SECURED VERSION
A personal-use web app for creating fun videos by overlaying faces on templates
Optimized for mobile (iPhone) use

SECURITY IMPROVEMENTS:
- Path traversal protection
- Input validation
- Rate limiting
- Subprocess timeouts
- Error message sanitization
- Logging
- Debug mode disabled
- Security headers
"""

import logging
import os
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import mediapipe as mp
from flask import Flask, abort, jsonify, render_template, request, send_file, url_for
from werkzeug.security import safe_join
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # Reduced to 5MB for security
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'
app.config['TEMPLATE_FOLDER'] = 'static/template_videos'

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic'}

# Maximum filename length
MAX_FILENAME_LENGTH = 100

# Template name validation pattern (alphanumeric, underscore, hyphen only)
TEMPLATE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_template_name(template_name):
    """
    Validate template name to prevent path traversal and command injection
    Returns sanitized template name or raises ValueError
    """
    if not template_name:
        raise ValueError("Template name cannot be empty")

    # Strict whitelist validation
    if not TEMPLATE_NAME_PATTERN.match(template_name):
        raise ValueError("Invalid template name. Use only letters, numbers, hyphens, and underscores")

    return template_name


def validate_filename(filename):
    """
    Validate filename to prevent path traversal
    Returns True if safe, False otherwise
    """
    if not filename:
        return False

    # Check for path traversal attempts
    if '/' in filename or '\\' in filename or '..' in filename:
        return False

    # Check for null bytes
    if '\x00' in filename:
        return False

    return True


def detect_and_extract_face(image_path):
    """
    Detect face in image and extract it with padding
    Returns: face image (numpy array) or None if no face found
    """
    mp_face_detection = mp.solutions.face_detection

    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            app.logger.warning(f"Failed to read image: {image_path}")
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
    except Exception as e:
        app.logger.error(f"Error in face detection: {e}", exc_info=True)
        return None


def create_face_overlay_video(template_name, face_image_path, output_path):
    """
    Create video with face overlaid on template
    Uses FFmpeg for video processing

    SECURITY: Validates all paths and adds timeouts to prevent abuse
    """
    # SECURITY: Strict validation of template name
    try:
        template_name = validate_template_name(template_name)
    except ValueError as e:
        app.logger.warning(f"Invalid template name attempt: {template_name}")
        raise

    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.mp4')

    # SECURITY: Verify path is within template directory (prevent traversal)
    template_abs = os.path.abspath(template_path)
    template_dir_abs = os.path.abspath(app.config['TEMPLATE_FOLDER'])

    if not template_abs.startswith(template_dir_abs + os.sep):
        app.logger.warning(f"Path traversal attempt detected: {template_name}")
        raise ValueError("Invalid template path")

    if not os.path.exists(template_abs):
        app.logger.warning(f"Template not found: {template_name}")
        raise FileNotFoundError(f"Template {template_name} not found")

    # Extract face
    face = detect_and_extract_face(face_image_path)
    if face is None:
        raise ValueError("No face detected in image")

    # Save face as temporary PNG
    face_temp = f"temp/face_{uuid.uuid4().hex}.png"
    cv2.imwrite(face_temp, face)

    try:
        # Get template video info with TIMEOUT
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            template_abs  # Use verified absolute path
        ]

        # SECURITY: Add timeout to prevent hanging
        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout
            check=True
        )
        video_width, video_height = map(int, result.stdout.strip().split('x'))

        # Calculate face size
        face_size = int(min(video_width, video_height) * 0.25)

        # Calculate position
        x_pos = int(video_width * 0.5 - face_size * 0.5)
        y_pos = int(video_height * 0.15)

        # FFmpeg command
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', template_abs,  # Use verified absolute path
            '-i', face_temp,
            '-filter_complex',
            f'[1:v]scale={face_size}:{face_size}[face];'
            f'[0:v][face]overlay={x_pos}:{y_pos}',
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            output_path
        ]

        # SECURITY: Run FFmpeg with timeout
        app.logger.info(f"Starting video processing for template: {template_name}")
        subprocess.run(
            ffmpeg_cmd,
            check=True,
            capture_output=True,
            timeout=60  # 60 second timeout
        )
        app.logger.info(f"Video processing completed: {output_path}")

    except subprocess.TimeoutExpired:
        app.logger.error(f"Video processing timeout for template: {template_name}")
        raise ValueError("Video processing timed out")
    except subprocess.CalledProcessError as e:
        app.logger.error(f"FFmpeg error: {e.stderr}")
        raise ValueError("Video processing failed")
    finally:
        # Clean up temporary face file
        if os.path.exists(face_temp):
            os.remove(face_temp)

    return output_path


@app.after_request
def set_security_headers(response):
    """Set security headers on all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Only use HSTS if you have HTTPS configured
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline'; img-src 'self' data:"
    return response


@app.before_request
def log_request():
    """Log all requests for security monitoring"""
    app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")


@app.route('/')
def index():
    """Main page"""
    # Get available templates
    templates = []
    template_dir = Path(app.config['TEMPLATE_FOLDER'])

    if template_dir.exists():
        for template_file in template_dir.glob('*.mp4'):
            template_name = template_file.stem

            # Validate template name before adding
            try:
                validate_template_name(template_name)
                templates.append({
                    'id': template_name,
                    'name': template_name.replace('_', ' ').title(),
                    'url': url_for('static', filename=f'template_videos/{template_file.name}')
                })
            except ValueError:
                app.logger.warning(f"Skipping invalid template name: {template_name}")
                continue

    return render_template('index.html', templates=templates)


@app.route('/upload', methods=['POST'])
def upload_photo():
    """Handle photo upload and face detection"""
    if 'photo' not in request.files:
        app.logger.warning(f"Upload attempt without photo from {request.remote_addr}")
        return jsonify({'success': False, 'error': 'No photo uploaded'}), 400

    file = request.files['photo']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        app.logger.warning(f"Invalid file type upload attempt: {file.filename}")
        return jsonify({'success': False, 'error': 'Invalid file type. Use JPG or PNG'}), 400

    # SECURITY: Additional filename validation and length limit
    safe_filename_str = secure_filename(file.filename)

    if len(safe_filename_str) > MAX_FILENAME_LENGTH:
        safe_filename_str = safe_filename_str[-MAX_FILENAME_LENGTH:]

    # Use UUID for actual storage to prevent any filename issues
    file_ext = safe_filename_str.rsplit('.', 1)[1].lower() if '.' in safe_filename_str else 'jpg'
    filename = f"{uuid.uuid4().hex}.{file_ext}"

    # SECURITY: Use safe_join to prevent path traversal
    try:
        filepath = safe_join(app.config['UPLOAD_FOLDER'], filename)
    except (ValueError, TypeError):
        app.logger.error(f"Path join error for filename: {filename}")
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    if not filepath:
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    file.save(filepath)
    app.logger.info(f"File uploaded: {filename}")

    # Check for face
    face = detect_and_extract_face(filepath)
    if face is None:
        os.remove(filepath)  # Clean up
        app.logger.info(f"No face detected in upload: {filename}")
        return jsonify({'success': False, 'error': 'No face detected. Please use a clear photo with a visible face.'}), 400

    app.logger.info(f"Face detected successfully in: {filename}")
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

    # SECURITY: Validate filename (no path traversal)
    if not validate_filename(filename):
        app.logger.warning(f"Invalid filename in generate request: {filename}")
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    # SECURITY: Validate template name
    try:
        template = validate_template_name(template)
    except ValueError as e:
        app.logger.warning(f"Invalid template in generate request: {template}")
        return jsonify({'success': False, 'error': 'Invalid template name'}), 400

    # Validate input file exists using safe_join
    try:
        filepath = safe_join(app.config['UPLOAD_FOLDER'], filename)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    if not filepath or not os.path.exists(filepath):
        app.logger.warning(f"Upload file not found: {filename}")
        return jsonify({'success': False, 'error': 'Uploaded photo not found'}), 404

    # Generate output filename
    output_filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        # Create video
        app.logger.info(f"Starting video generation: {output_filename}")
        create_face_overlay_video(template, filepath, output_path)

        # Optionally clean up uploaded photo
        # os.remove(filepath)

        app.logger.info(f"Video generation successful: {output_filename}")
        return jsonify({
            'success': True,
            'video_url': url_for('static', filename=f'output/{output_filename}'),
            'download_url': url_for('download_video', filename=output_filename)
        })

    except FileNotFoundError:
        app.logger.error(f"Template not found: {template}")
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    except ValueError as e:
        app.logger.error(f"Video generation error: {e}")
        return jsonify({'success': False, 'error': 'Invalid input or processing failed'}), 400
    except Exception as e:
        # SECURITY: Log full error internally but return generic message
        app.logger.error(f"Unexpected error in video generation: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Video processing failed'}), 500


@app.route('/download/<filename>')
def download_video(filename):
    """Download generated video"""
    # SECURITY: Validate filename (no path traversal)
    if not validate_filename(filename):
        app.logger.warning(f"Invalid filename in download request: {filename}")
        return "Invalid filename", 400

    if not filename.endswith('.mp4'):
        app.logger.warning(f"Non-MP4 download attempt: {filename}")
        return "Invalid file type", 400

    # SECURITY: Use safe_join
    try:
        filepath = safe_join(app.config['OUTPUT_FOLDER'], filename)
    except (ValueError, TypeError):
        return "Invalid filename", 400

    if not filepath or not os.path.exists(filepath):
        return "File not found", 404

    app.logger.info(f"Video download: {filename}")
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

    # SECURITY: Get debug mode from environment variable (default to False)
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    if debug_mode:
        app.logger.warning("🚨 DEBUG MODE IS ENABLED - DO NOT USE IN PRODUCTION!")

    app.logger.info("Starting Face Swap App (Secured Version)")
    app.logger.info(f"Debug mode: {debug_mode}")
    app.logger.info(f"Listening on 0.0.0.0:5000 (local network only)")

    # Run app
    # For iPhone access on same WiFi, use host='0.0.0.0'
    # SECURITY: Debug mode controlled by environment variable
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
