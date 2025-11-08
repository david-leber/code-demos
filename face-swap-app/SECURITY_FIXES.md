# Critical Security Fixes - Quick Implementation Guide

⚠️ **IMPLEMENT THESE BEFORE PUBLIC DEPLOYMENT**

These are the minimum security fixes required to make the app safer for internet exposure. This is NOT a complete security solution, but addresses the most critical vulnerabilities.

---

## Fix 1: Path Traversal Protection (CRITICAL)

**File**: `app.py`

Add import:
```python
import re
from werkzeug.security import safe_join
```

Replace the `generate_video` function:
```python
@app.route('/generate', methods=['POST'])
def generate_video():
    """Generate video with face overlay"""
    data = request.get_json()

    if not data or 'filename' not in data or 'template' not in data:
        return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

    filename = data['filename']
    template = data['template']

    # SECURITY: Validate filename (no path traversal)
    if '/' in filename or '\\' in filename or '..' in filename:
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    # SECURITY: Validate template name (whitelist only)
    if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', template):
        return jsonify({'success': False, 'error': 'Invalid template name'}), 400

    # Validate inputs
    try:
        filepath = safe_join(app.config['UPLOAD_FOLDER'], filename)
    except (ValueError, SecurityError):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    if not filepath or not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Uploaded photo not found'}), 404

    # Generate output filename
    output_filename = f"video_{uuid.uuid4().hex}.mp4"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

    try:
        # Create video
        create_face_overlay_video(template, filepath, output_path)

        return jsonify({
            'success': True,
            'video_url': url_for('static', filename=f'output/{output_filename}'),
            'download_url': url_for('download_video', filename=output_filename)
        })

    except FileNotFoundError:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    except ValueError as e:
        return jsonify({'success': False, 'error': 'Invalid input'}), 400
    except Exception as e:
        # Log full error internally but return generic message
        app.logger.error(f"Video generation error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Video processing failed'}), 500
```

Replace the `download_video` function:
```python
@app.route('/download/<filename>')
def download_video(filename):
    """Download generated video"""
    # SECURITY: Validate filename (no path traversal)
    if '/' in filename or '\\' in filename or '..' in filename:
        return "Invalid filename", 400

    if not filename.endswith('.mp4'):
        return "Invalid file type", 400

    try:
        filepath = safe_join(app.config['OUTPUT_FOLDER'], filename)
    except (ValueError, Exception):
        return "Invalid filename", 400

    if not filepath or not os.path.exists(filepath):
        return "File not found", 404

    return send_file(filepath, as_attachment=True, download_name=f"face_swap_{filename}")
```

Update `create_face_overlay_video`:
```python
def create_face_overlay_video(template_name, face_image_path, output_path):
    """
    Create video with face overlaid on template
    Uses FFmpeg for video processing
    """
    # SECURITY: Strict validation of template name
    if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', template_name):
        raise ValueError("Invalid template name")

    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.mp4')

    # SECURITY: Verify path is within template directory (prevent traversal)
    template_abs = os.path.abspath(template_path)
    template_dir_abs = os.path.abspath(app.config['TEMPLATE_FOLDER'])

    if not template_abs.startswith(template_dir_abs + os.sep):
        raise ValueError("Invalid template path")

    if not os.path.exists(template_abs):
        raise FileNotFoundError(f"Template {template_name} not found")

    # Extract face
    face = detect_and_extract_face(face_image_path)
    if face is None:
        raise ValueError("No face detected in image")

    # Save face as temporary PNG
    face_temp = f"temp/face_{uuid.uuid4().hex}.png"
    cv2.imwrite(face_temp, face)

    try:
        # Get template video info with timeout
        probe_cmd = [
            'ffprobe', '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=s=x:p=0',
            template_abs  # Use verified absolute path
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
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

        # Run FFmpeg with timeout
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, timeout=60)

    finally:
        # Clean up temporary face file
        if os.path.exists(face_temp):
            os.remove(face_temp)

    return output_path
```

---

## Fix 2: Rate Limiting (CRITICAL)

**Install dependency**:
```bash
pip install Flask-Limiter
```

**File**: `app.py`

Add after imports:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # Use Redis in production: "redis://localhost:6379"
)
```

Add decorators to routes:
```python
@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")  # Max 10 uploads per minute
def upload_photo():
    # ... existing code

@app.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 videos per minute (expensive operation)
def generate_video():
    # ... existing code
```

---

## Fix 3: Disable Debug Mode (CRITICAL)

**File**: `app.py`

Replace the last block:
```python
if __name__ == '__main__':
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TEMPLATE_FOLDER'], exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    # NEVER use debug=True in production!
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

---

## Fix 4: CSRF Protection (HIGH PRIORITY)

**Install dependency**:
```bash
pip install Flask-WTF
```

**File**: `app.py`

Add after app creation:
```python
from flask_wtf.csrf import CSRFProtect
import secrets

# CSRF protection
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
csrf = CSRFProtect(app)
```

**File**: `templates/index.html`

Add CSRF token to the HTML head:
```html
<head>
    <!-- ... existing head content ... -->
    <meta name="csrf-token" content="{{ csrf_token() }}">
</head>
```

Update JavaScript to include CSRF token:
```javascript
// Add this function at the top of the script section
function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
}

// Update all fetch calls to include CSRF token
async function handlePhotoUpload() {
    const file = photoInput.files[0];
    if (!file) return;

    // ... existing preview code ...

    const formData = new FormData();
    formData.append('photo', file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()  // Add CSRF token
            }
        });
        // ... rest of existing code
    }
}

// Update generate video fetch
generateBtn.addEventListener('click', async () => {
    // ... existing code ...

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()  // Add CSRF token
            },
            body: JSON.stringify({
                filename: uploadedFilename,
                template: selectedTemplate
            })
        });
        // ... rest of existing code
    }
});
```

---

## Fix 5: Add Security Headers (HIGH PRIORITY)

**File**: `app.py`

Add after app creation:
```python
@app.after_request
def set_security_headers(response):
    """Set security headers on all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline'"
    return response
```

---

## Fix 6: Add Basic Authentication (HIGH PRIORITY)

**Install dependency**:
```bash
pip install Flask-HTTPAuth
```

**File**: `app.py`

Add imports:
```python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
```

Add authentication:
```python
auth = HTTPBasicAuth()

# In production, use environment variables or database
users = {
    "admin": generate_password_hash("CHANGE_THIS_PASSWORD")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Protect routes
@app.route('/upload', methods=['POST'])
@auth.login_required
@limiter.limit("10 per minute")
def upload_photo():
    # ... existing code

@app.route('/generate', methods=['POST'])
@auth.login_required
@limiter.limit("5 per minute")
def generate_video():
    # ... existing code

@app.route('/download/<filename>')
@auth.login_required
def download_video(filename):
    # ... existing code
```

---

## Fix 7: Add Logging (MEDIUM PRIORITY)

**File**: `app.py`

Add at the top:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app.logger.setLevel(logging.INFO)
```

Add logging to critical operations:
```python
@app.route('/upload', methods=['POST'])
@auth.login_required
@limiter.limit("10 per minute")
def upload_photo():
    """Handle photo upload and face detection"""
    app.logger.info(f"Upload attempt from {request.remote_addr}")

    # ... existing upload code ...

    if face is None:
        os.remove(filepath)
        app.logger.warning(f"No face detected in upload from {request.remote_addr}")
        return jsonify({...}), 400

    app.logger.info(f"Successful upload: {filename}")
    return jsonify({...})
```

---

## Fix 8: File Cleanup (MEDIUM PRIORITY)

**Install dependency**:
```bash
pip install APScheduler
```

**File**: `app.py`

Add import:
```python
from apscheduler.schedulers.background import BackgroundScheduler
import time
```

Add cleanup function:
```python
def cleanup_old_files():
    """Delete files older than 24 hours"""
    cutoff = time.time() - (24 * 60 * 60)

    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], 'temp']:
        if not os.path.exists(folder):
            continue

        for filename in os.listdir(folder):
            if filename == '.gitkeep':
                continue

            filepath = os.path.join(folder, filename)
            try:
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    app.logger.info(f"Cleaned up old file: {filepath}")
            except Exception as e:
                app.logger.error(f"Error cleaning up {filepath}: {e}")
```

Add to main block:
```python
if __name__ == '__main__':
    # ... existing directory creation ...

    # Start background file cleanup scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=cleanup_old_files, trigger="interval", hours=1)
    scheduler.start()

    try:
        app.run(host='0.0.0.0', port=5000, debug=debug_mode)
    finally:
        scheduler.shutdown()
```

---

## Fix 9: Use Production WSGI Server (CRITICAL FOR PRODUCTION)

**DO NOT use Flask's development server in production!**

**Install**:
```bash
pip install gunicorn
```

**Run with**:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

Or create `gunicorn_config.py`:
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
errorlog = "gunicorn_error.log"
accesslog = "gunicorn_access.log"
loglevel = "info"
```

Run with:
```bash
gunicorn -c gunicorn_config.py app:app
```

---

## Fix 10: Environment Variables (MEDIUM PRIORITY)

**Create `.env` file** (never commit this!):
```bash
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-generate-with-secrets.token_hex(32)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password-here
MAX_CONTENT_LENGTH=5242880  # 5MB
```

**Install**:
```bash
pip install python-dotenv
```

**File**: `app.py`

Add at top:
```python
from dotenv import load_dotenv

load_dotenv()

# Use environment variables
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16777216))
```

---

## Updated Requirements

**File**: `requirements.txt`

Add these dependencies:
```txt
Flask==3.0.0
opencv-python==4.8.1.78
mediapipe==0.10.8
Pillow==10.1.0
numpy==1.24.3
werkzeug==3.0.1

# Security & Production
Flask-Limiter==3.5.0
Flask-WTF==1.2.1
Flask-HTTPAuth==4.8.0
gunicorn==21.2.0
python-dotenv==1.0.0
APScheduler==3.10.4

# Testing dependencies
pytest==7.4.3
pytest-cov==4.1.0
pytest-flask==1.3.0
```

---

## Deployment Checklist

Before deploying to production:

- [ ] All critical fixes implemented
- [ ] Debug mode disabled (`debug=False`)
- [ ] Using gunicorn or uWSGI (NOT Flask dev server)
- [ ] HTTPS configured (SSL certificate)
- [ ] Firewall configured (only ports 80/443 open)
- [ ] Strong passwords set for admin accounts
- [ ] Environment variables configured
- [ ] Logging enabled and monitored
- [ ] Rate limiting configured
- [ ] File cleanup scheduled
- [ ] Backups configured
- [ ] Security headers enabled
- [ ] CSRF protection enabled
- [ ] Path traversal fixes verified
- [ ] Penetration testing completed
- [ ] Privacy policy and terms of service added

---

## Quick Start (Secure Version)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export FLASK_DEBUG=False
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

3. Run with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
```

4. Set up reverse proxy (nginx) with HTTPS

5. Configure firewall and monitoring

---

## Still Not Safe Enough?

Even with all these fixes, for sensitive production use you should:

1. **Hire a security professional** for code review
2. **Run penetration testing** before launch
3. **Use a WAF** (Web Application Firewall)
4. **Implement proper authentication** (OAuth, JWT)
5. **Move to cloud storage** (S3, not local disk)
6. **Add job queue** (Celery) for video processing
7. **Implement audit logging**
8. **Get security insurance**

---

**Remember**: Security is not a one-time fix, it's an ongoing process!
