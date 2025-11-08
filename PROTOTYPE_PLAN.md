# Rapid Prototype Plan - JibJab-Style Video App

## Prototype Goal

Build a minimal working demo in **5-7 days** that demonstrates:
1. Upload a photo with a face
2. Select a simple video template
3. Generate a video with the face swapped onto the template
4. Play back the result

**NOT included in prototype**: Authentication, databases, payment, mobile apps, production infrastructure

---

## Prototype Architecture (Simplified)

```
┌─────────────────────────────────────┐
│     Simple Web UI (HTML/JS)         │
│  - File upload                      │
│  - Template selection               │
│  - Video playback                   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│   Local Python Flask Server         │
│  - Receive image upload             │
│  - Face detection (MediaPipe)       │
│  - Video processing (FFmpeg)        │
│  - Return processed video           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│      Local File System              │
│  - Input images                     │
│  - Template videos (2-3 samples)    │
│  - Output videos                    │
└─────────────────────────────────────┘
```

---

## Technology Stack (Prototype)

### Frontend
- **Pure HTML/CSS/JavaScript** (no frameworks needed)
- **Bootstrap** for quick styling
- **HTML5 `<video>` element** for playback
- **Fetch API** for uploads

### Backend
- **Python 3.9+** (easier for ML/CV work)
- **Flask** (lightweight web server)
- **MediaPipe** (Google's face detection - easy to use)
- **OpenCV** (image processing)
- **FFmpeg** (video manipulation via command line)

### Why This Stack?
- ✅ Python best for rapid CV prototyping
- ✅ MediaPipe has excellent face detection out-of-the-box
- ✅ No database needed (file-based)
- ✅ Can run entirely locally
- ✅ Easy to iterate and debug

---

## Prototype Features

### Included (MVP)
- ✅ Single photo upload
- ✅ Face detection on uploaded photo
- ✅ 2-3 hardcoded video templates (5-10 seconds each)
- ✅ Basic face overlay on template video
- ✅ Video playback in browser
- ✅ Download generated video

### Explicitly NOT Included
- ❌ User authentication
- ❌ Database
- ❌ Multiple faces
- ❌ Advanced face blending
- ❌ Cloud deployment
- ❌ Template library management
- ❌ Queue system
- ❌ Progress bars (synchronous processing)
- ❌ Social sharing
- ❌ Mobile responsiveness

---

## 5-Day Implementation Plan

### Day 1: Environment Setup & Face Detection

**Tasks:**
1. Set up Python virtual environment
2. Install dependencies:
   ```bash
   pip install flask opencv-python mediapipe pillow
   ```
3. Create basic Flask app structure
4. Implement face detection endpoint
5. Test with sample images

**Deliverable:** Working face detection API that returns face coordinates

**Code Structure:**
```
prototype/
├── app.py                 # Flask app
├── face_detector.py       # MediaPipe face detection
├── requirements.txt
├── static/
│   ├── uploads/          # User uploaded images
│   ├── templates/        # Video templates
│   └── output/           # Generated videos
└── templates/
    └── index.html        # Web UI
```

**Face Detection Test:**
```python
# face_detector.py
import mediapipe as mp
import cv2

def detect_face(image_path):
    """Returns face bounding box and landmarks"""
    mp_face_detection = mp.solutions.face_detection
    mp_face_mesh = mp.solutions.face_mesh

    image = cv2.imread(image_path)

    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as face_detection:
        results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.detections:
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            return {
                'x': bbox.xmin,
                'y': bbox.ymin,
                'width': bbox.width,
                'height': bbox.height
            }
    return None
```

---

### Day 2: Simple Face Overlay (Static Image Test)

**Tasks:**
1. Extract face from uploaded photo
2. Create template with face region marked
3. Resize and position face onto template
4. Test basic overlay on single image frame
5. Refine positioning and scaling

**Deliverable:** Successfully overlay user face onto a single image

**Approach:**
```python
# face_overlay.py
def overlay_face(source_image_path, target_image_path, face_region):
    """
    Simple approach: Extract face, resize, paste onto target
    """
    source = cv2.imread(source_image_path)
    target = cv2.imread(target_image_path)

    # Extract face from source
    face = extract_face(source, face_region)

    # Resize to match target region
    face_resized = cv2.resize(face, (target_width, target_height))

    # Simple paste (no blending initially)
    target[y:y+height, x:x+width] = face_resized

    return target
```

**Test Data:**
- Use a single frame from video template
- Manually define face region coordinates
- Verify face appears in correct position

---

### Day 3: Video Template Preparation & Frame Extraction

**Tasks:**
1. Select/create 2-3 simple video templates:
   - Dancing person (5 seconds)
   - Waving person (3 seconds)
   - Nodding head (3 seconds)
2. Extract frames from template videos using FFmpeg
3. Manually mark face regions for each template
4. Create template metadata file
5. Test frame extraction pipeline

**Deliverable:** Template videos with face tracking data

**FFmpeg Frame Extraction:**
```bash
# Extract all frames from video
ffmpeg -i template1.mp4 -vf fps=30 frames/frame_%04d.png

# Extract every 3rd frame (10fps) for faster processing
ffmpeg -i template1.mp4 -vf fps=10 frames/frame_%04d.png
```

**Template Metadata (Simple JSON):**
```json
{
  "id": "dance_1",
  "name": "Dance Move",
  "video_path": "static/templates/dance.mp4",
  "duration": 5,
  "fps": 10,
  "face_regions": [
    {
      "frame": 1,
      "x": 320,
      "y": 180,
      "width": 200,
      "height": 240
    },
    {
      "frame": 2,
      "x": 325,
      "y": 175,
      "width": 200,
      "height": 240
    }
    // ... one entry per frame
  ]
}
```

**Simplified Approach:**
- Use **static face region** (assume face doesn't move much)
- OR manually track ~5 keyframes, interpolate the rest
- Focus on one good template first

---

### Day 4: Video Processing Pipeline

**Tasks:**
1. Process each video frame:
   - Load template frame
   - Overlay user face
   - Save processed frame
2. Reassemble frames into video with FFmpeg
3. Add audio from original template
4. Optimize for speed (frame skipping if needed)
5. Test end-to-end on one template

**Deliverable:** Generate first complete video with face swap

**Video Processing Script:**
```python
# video_processor.py
import cv2
import subprocess
import os

def process_video(template_id, user_face_path, output_path):
    """
    Main video processing function
    """
    # 1. Load template metadata
    template = load_template(template_id)

    # 2. Detect face in user image
    face_data = detect_face(user_face_path)
    if not face_data:
        raise Exception("No face detected")

    # 3. Extract user face
    user_face = extract_face(user_face_path, face_data)

    # 4. Process each frame
    temp_dir = "temp_frames/"
    os.makedirs(temp_dir, exist_ok=True)

    for i, frame_data in enumerate(template['face_regions']):
        # Load template frame
        frame = cv2.imread(f"templates/{template_id}/frame_{i:04d}.png")

        # Overlay face
        processed = overlay_face(
            user_face,
            frame,
            frame_data['x'],
            frame_data['y'],
            frame_data['width'],
            frame_data['height']
        )

        # Save processed frame
        cv2.imwrite(f"{temp_dir}/frame_{i:04d}.png", processed)

    # 5. Reassemble with FFmpeg
    subprocess.run([
        'ffmpeg',
        '-framerate', str(template['fps']),
        '-i', f'{temp_dir}/frame_%04d.png',
        '-i', template['video_path'],  # For audio
        '-map', '0:v',  # Video from frames
        '-map', '1:a',  # Audio from template
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-pix_fmt', 'yuv420p',
        output_path
    ])

    # 6. Cleanup temp files
    cleanup_temp_files(temp_dir)

    return output_path
```

---

### Day 5: Web UI & Integration

**Tasks:**
1. Create simple HTML upload form
2. Template selection UI (thumbnails)
3. Display processing status
4. Video playback
5. Download button
6. Polish UI with Bootstrap
7. End-to-end testing

**Deliverable:** Working web interface

**HTML UI (Simple):**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Face Swap Prototype</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-5">
        <h1>JibJab-Style Video Prototype</h1>

        <!-- Step 1: Upload Photo -->
        <div class="card mt-4">
            <div class="card-body">
                <h3>1. Upload Your Photo</h3>
                <input type="file" id="photoUpload" accept="image/*" class="form-control">
                <img id="preview" class="mt-3" style="max-width: 200px; display:none;">
            </div>
        </div>

        <!-- Step 2: Select Template -->
        <div class="card mt-4">
            <div class="card-body">
                <h3>2. Select Template</h3>
                <div class="row" id="templates">
                    <div class="col-md-4">
                        <div class="card template-card" data-template="dance_1">
                            <video class="card-img-top" muted loop autoplay>
                                <source src="/static/templates/dance.mp4">
                            </video>
                            <div class="card-body">
                                <button class="btn btn-primary">Select</button>
                            </div>
                        </div>
                    </div>
                    <!-- More templates... -->
                </div>
            </div>
        </div>

        <!-- Step 3: Generate -->
        <div class="card mt-4">
            <div class="card-body">
                <button id="generateBtn" class="btn btn-success btn-lg">Generate Video</button>
                <div id="processing" style="display:none;">
                    <p>Processing... (this may take 30-60 seconds)</p>
                </div>
            </div>
        </div>

        <!-- Step 4: Result -->
        <div class="card mt-4" id="result" style="display:none;">
            <div class="card-body">
                <h3>Your Video!</h3>
                <video id="outputVideo" controls style="max-width: 100%;">
                    <source id="outputSource" type="video/mp4">
                </video>
                <br>
                <a id="downloadBtn" class="btn btn-primary mt-3" download>Download</a>
            </div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
```

**JavaScript (app.js):**
```javascript
let uploadedPhoto = null;
let selectedTemplate = null;

document.getElementById('photoUpload').addEventListener('change', function(e) {
    const file = e.target.files[0];
    uploadedPhoto = file;

    // Preview
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('preview').src = e.target.result;
        document.getElementById('preview').style.display = 'block';
    };
    reader.readAsDataURL(file);
});

document.querySelectorAll('.template-card').forEach(card => {
    card.querySelector('button').addEventListener('click', function() {
        selectedTemplate = card.dataset.template;
        // Visual feedback
        document.querySelectorAll('.template-card').forEach(c =>
            c.classList.remove('border-success'));
        card.classList.add('border-success', 'border-3');
    });
});

document.getElementById('generateBtn').addEventListener('click', async function() {
    if (!uploadedPhoto || !selectedTemplate) {
        alert('Please upload a photo and select a template');
        return;
    }

    // Show processing
    document.getElementById('processing').style.display = 'block';
    this.disabled = true;

    // Upload and process
    const formData = new FormData();
    formData.append('photo', uploadedPhoto);
    formData.append('template', selectedTemplate);

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // Show result
            document.getElementById('outputSource').src = result.video_url;
            document.getElementById('outputVideo').load();
            document.getElementById('downloadBtn').href = result.video_url;
            document.getElementById('result').style.display = 'block';
            document.getElementById('processing').style.display = 'none';
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        alert('Processing failed: ' + error);
    } finally {
        this.disabled = false;
    }
});
```

**Flask Backend (app.py):**
```python
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
from video_processor import process_video
from face_detector import detect_face

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['OUTPUT_FOLDER'] = 'static/output'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Get uploaded photo
        photo = request.files['photo']
        template_id = request.form['template']

        # Save photo
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

        # Check for face
        face_data = detect_face(photo_path)
        if not face_data:
            return jsonify({'success': False, 'error': 'No face detected'})

        # Process video
        output_filename = f"output_{os.path.splitext(filename)[0]}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        process_video(template_id, photo_path, output_path)

        return jsonify({
            'success': True,
            'video_url': f'/static/output/{output_filename}'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

---

## Day 6-7: Testing, Refinement & Documentation

**Tasks:**
1. Test with various face photos (different angles, lighting)
2. Improve face positioning/scaling if needed
3. Add basic error handling
4. Create demo video of the prototype
5. Document limitations and next steps
6. Prepare demo presentation

**Testing Checklist:**
- [ ] Upload photo with clear frontal face → Works
- [ ] Upload photo with side profile → Handles gracefully
- [ ] Upload photo with no face → Shows error
- [ ] Upload photo with multiple faces → Picks first face
- [ ] Select each template → All work
- [ ] Download video → File is valid MP4
- [ ] Video has audio from template → Confirmed

**Known Limitations to Document:**
- Face blending is basic (no smooth edges)
- No handling of face orientation (works best with frontal faces)
- Processing is synchronous (blocks for 30-60 seconds)
- No color matching between face and video
- Single face only
- Manual face region tracking in templates

---

## Success Criteria

The prototype is successful if it demonstrates:

✅ **Core Concept Proof**: Shows that face swapping on video is feasible
✅ **End-to-End Flow**: User can upload → select → generate → view
✅ **Acceptable Quality**: Result is recognizable and somewhat convincing
✅ **Fast Enough**: Processing completes in under 2 minutes
✅ **Reproducible**: Works consistently with test images

**NOT required for prototype:**
- Production-ready code quality
- Perfect face blending
- Scalability
- Security
- Mobile support

---

## Required Assets for Prototype

### Video Templates (Create or Source)
Need 2-3 short videos with:
- Clear, frontal face visible throughout
- Simple background
- 3-10 seconds duration
- Minimal head movement
- Good lighting

**Options:**
1. **Record yourself**: Use phone to record simple movements
2. **Stock footage**: Sites like Pexels, Pixabay (free, CC0)
3. **Generate with AI**: Use tools like D-ID or Synthesia for simple animations

**Example Template Ideas:**
- Person waving at camera
- Person nodding yes/no
- Person dancing (minimal movement)
- Person giving thumbs up

### Test Photos
Collect 5-10 test images with:
- Clear frontal faces
- Good lighting
- Various ages/genders
- Different skin tones
- Some edge cases (sunglasses, hats)

**Sources:**
- This Person Does Not Exist (AI-generated faces)
- Free stock photo sites
- Your own photos (with permission)

---

## File Structure

```
jibjab-prototype/
├── app.py                          # Flask web server
├── face_detector.py                # MediaPipe face detection
├── face_overlay.py                 # Face extraction and overlay
├── video_processor.py              # Main video processing pipeline
├── requirements.txt                # Python dependencies
├── README.md                       # Prototype documentation
│
├── templates/
│   └── index.html                  # Web UI
│
├── static/
│   ├── app.js                      # Frontend JavaScript
│   ├── style.css                   # Custom styles
│   │
│   ├── templates/                  # Video templates
│   │   ├── dance/
│   │   │   ├── video.mp4
│   │   │   ├── metadata.json
│   │   │   └── frames/             # Extracted frames
│   │   │       ├── frame_0001.png
│   │   │       └── ...
│   │   └── wave/
│   │       └── ...
│   │
│   ├── uploads/                    # User uploaded photos (gitignore)
│   └── output/                     # Generated videos (gitignore)
│
└── tests/
    ├── test_face_detection.py
    ├── test_overlay.py
    └── sample_images/              # Test images
```

---

## Installation & Setup

### Prerequisites
```bash
# Python 3.9+
python --version

# FFmpeg
ffmpeg -version

# If not installed:
# macOS: brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: Download from ffmpeg.org
```

### Quick Start
```bash
# 1. Clone/create project
mkdir jibjab-prototype
cd jibjab-prototype

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install flask opencv-python mediapipe pillow numpy

# 4. Create directory structure
mkdir -p static/{uploads,output,templates}
mkdir -p templates

# 5. Run server
python app.py

# 6. Open browser
# http://localhost:5000
```

---

## Risk Mitigation

### Technical Risks

**Risk**: Face detection fails on many images
- **Mitigation**: Use MediaPipe (highly robust), provide user feedback, allow manual face selection in v2

**Risk**: Face overlay looks unrealistic
- **Mitigation**: Set expectations (this is a prototype), focus on proof-of-concept, improve in later iterations

**Risk**: Video processing too slow
- **Mitigation**: Reduce frame rate (10 fps), limit template duration (5-10 seconds), process fewer frames

**Risk**: FFmpeg issues on different systems
- **Mitigation**: Test on Mac/Windows/Linux early, provide clear installation instructions

### Scope Risks

**Risk**: Feature creep (trying to add too much)
- **Mitigation**: Stick strictly to 5-day plan, create "v2 features" list for later

**Risk**: Perfect face blending rabbit hole
- **Mitigation**: Accept "good enough" for prototype, focus on end-to-end flow

---

## Next Steps After Prototype

Once prototype is working, evaluate:

1. **Quality Assessment**
   - Is face swapping quality acceptable?
   - Do we need better algorithms or is simple overlay sufficient?

2. **Performance Analysis**
   - How long does processing take?
   - Can we optimize or do we need cloud processing?

3. **User Feedback**
   - Show to 5-10 people
   - What do they like/dislike?
   - Would they use this?

4. **Technical Decisions**
   - Stick with Python backend or move to Node.js?
   - Use third-party API (Reface, DeepAI) instead of building?
   - Client-side processing (WebAssembly + TensorFlow.js) viable?

5. **Build vs Buy**
   - Continue custom development?
   - License existing technology?
   - Partner with face-swap API provider?

---

## Alternative: Even Faster Prototype (2-3 Days)

If 5 days is too long, consider:

### Ultra-Minimal Approach
1. **Use existing face-swap API** (Reface API, DeepAI, etc.)
2. **Just build the UI** and API integration
3. **Skip video processing** - use API's capabilities
4. **No local setup** - deploy to cloud immediately

**Pros:**
- Can be done in 2-3 days
- Higher quality face swapping
- No ML expertise needed
- Easier to demo

**Cons:**
- Dependent on third-party service
- Monthly costs ($0.05-0.50 per video)
- Less control over quality
- Limited customization

---

## Resources & References

### MediaPipe Documentation
- [Face Detection Guide](https://google.github.io/mediapipe/solutions/face_detection.html)
- [Face Mesh Guide](https://google.github.io/mediapipe/solutions/face_mesh.html)

### FFmpeg Commands
- [FFmpeg Documentation](https://ffmpeg.org/ffmpeg.html)
- [Common video operations](https://trac.ffmpeg.org/wiki)

### Stock Video Sources
- [Pexels Videos](https://www.pexels.com/videos/) - Free stock videos
- [Pixabay Videos](https://pixabay.com/videos/) - Free videos
- [Mixkit](https://mixkit.co/) - Free video clips

### Face Swap Alternatives/References
- [DeepFaceLab](https://github.com/iperov/DeepFaceLab) - High quality, complex
- [FaceSwap](https://github.com/deepfakes/faceswap) - Open source
- [First Order Motion Model](https://github.com/AliaksandrSiarohin/first-order-model) - Animation transfer

---

## Budget Estimate

### Prototype Phase (No Cost)
- ✅ All open-source tools (free)
- ✅ Local development (no hosting)
- ✅ No paid APIs
- ✅ Free stock video templates

**Total: $0**

### Optional Paid Services (If Needed)
- **Better face swap API**: $50-200 for testing credits
- **Stock video licenses**: $0-50 for premium templates
- **Cloud hosting for demo**: $10-20/month (Heroku, Railway)

**Total: $0-$270**

---

## Timeline Summary

| Day | Focus | Deliverable |
|-----|-------|-------------|
| 1 | Setup & Face Detection | Working face detection API |
| 2 | Face Overlay | Face on single image |
| 3 | Template Preparation | Template videos with tracking data |
| 4 | Video Processing | First complete video generated |
| 5 | Web UI | Working web interface |
| 6-7 | Testing & Polish | Demo-ready prototype |

**Total Time: 5-7 days of focused work**

---

## Success Metrics

At the end of the prototype phase, we should be able to:

1. ✅ Demo the full flow in under 3 minutes
2. ✅ Generate a video that makes people smile/laugh
3. ✅ Show to stakeholders and get clear feedback
4. ✅ Make informed decision about full development
5. ✅ Identify technical challenges early

**This prototype is NOT production-ready, but it proves the concept works!**

---

**Document Version**: 1.0
**Created**: 2025-11-08
**Estimated Effort**: 5-7 days
**Prerequisites**: Python, FFmpeg, basic web development knowledge
**Status**: Ready to implement
