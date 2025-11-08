# 🎭 Face Swap Fun - Personal Video Creator

A simple, fun web app for creating videos by overlaying your face (or your friends'/family's faces) onto video templates. **Optimized for iPhone** and mobile use!

Think JibJab-style videos, but personal and simple.

## ✨ Features

- 📸 **Easy Photo Upload** - Take a photo or upload from your camera roll
- 🎬 **Video Templates** - Choose from fun video templates
- 🤖 **Automatic Face Detection** - AI detects and extracts faces automatically
- 📱 **Mobile Optimized** - Works great on iPhone and other mobile devices
- 🎉 **Quick Results** - Get your video in 10-30 seconds
- 💾 **Download & Share** - Save videos or share directly (on supported devices)

## 🚀 Quick Start

### Prerequisites

You need:
1. **Python 3.9+** - [Download here](https://www.python.org/downloads/)
2. **FFmpeg** - Video processing tool

#### Install FFmpeg:

**On macOS:**
```bash
brew install ffmpeg
```

**On Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Or use chocolatey: `choco install ffmpeg`

**On Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

Verify installation:
```bash
ffmpeg -version
```

### Installation

1. **Navigate to the app directory:**
```bash
cd face-swap-app
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv

# Activate it:
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

4. **Add template videos** (see below)

### Running the App

**Start the server:**
```bash
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

**Access from your computer:**
- Open browser and go to: `http://localhost:5000`

**Access from your iPhone (same WiFi):**
1. Find your computer's IP address:
   - **Mac**: System Settings → Network → Your IP is shown
   - **Windows**: Open CMD → type `ipconfig` → look for IPv4 Address
   - **Linux**: `ip addr` or `hostname -I`

2. On your iPhone, open Safari and go to:
   ```
   http://YOUR_COMPUTER_IP:5000
   ```
   For example: `http://192.168.1.100:5000`

3. Bookmark it for easy access!

**Optional: Add to iPhone Home Screen**
1. Open the app in Safari
2. Tap the Share button
3. Select "Add to Home Screen"
4. Now it opens like a native app!

## 🎬 Adding Template Videos

The app needs video templates to work. Here's how to add them:

### Option 1: Record Your Own (Recommended for Personal Use)

1. **Use your phone to record short videos (3-10 seconds):**
   - Stand in good lighting
   - Keep your face visible and forward-facing
   - Keep background simple
   - Ideas:
     - Dancing or grooving
     - Waving at camera
     - Nodding yes/no
     - Thumbs up
     - Funny face expressions

2. **Transfer videos to your computer**

3. **Save as MP4 files in the templates folder:**
   ```bash
   # Move/copy your videos here:
   face-swap-app/static/template_videos/

   # Examples:
   # dance_1.mp4
   # wave_hello.mp4
   # thumbs_up.mp4
   ```

4. **Restart the server** to see your new templates

### Option 2: Download Free Stock Videos

Download from these free sources:
- [Pexels Videos](https://www.pexels.com/videos/) - Search "person waving" or "person dancing"
- [Pixabay Videos](https://pixabay.com/videos/) - Free stock videos
- [Mixkit](https://mixkit.co/) - Free video clips

**Tips for selecting templates:**
- Short duration (3-10 seconds)
- Clear face visible throughout
- Person facing camera
- Good lighting
- Simple background
- Not too much movement

### Template File Naming

The filename becomes the template name in the UI:
- `dance_1.mp4` → "Dance 1"
- `wave_hello.mp4` → "Wave Hello"
- `funny_face.mp4` → "Funny Face"

## 📱 How to Use

1. **Upload a Photo**
   - Tap the upload area
   - Take a photo with your camera OR choose from photos
   - App will detect if there's a face

2. **Pick a Template**
   - Tap on a template video
   - It will highlight with a blue border

3. **Generate Video**
   - Tap "Generate Video"
   - Wait 10-30 seconds
   - Your video is ready!

4. **Download or Share**
   - Tap Download to save to your device
   - Tap Share to send via messages/social media (on supported devices)

5. **Make Another**
   - Tap "Create Another Video" to start over

## 🎨 Customization

### Adjust Face Size and Position

Edit `app.py` around line 125:

```python
# Make face bigger/smaller (0.25 = 25% of video size)
face_size = int(min(video_width, video_height) * 0.25)

# Move face position
x_pos = int(video_width * 0.5 - face_size * 0.5)  # Horizontal (0.5 = center)
y_pos = int(video_height * 0.15)  # Vertical (0.15 = near top)
```

### Change Upload Limit

Edit `app.py` line 16:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

### Modify Colors/Style

Edit `templates/index.html` - CSS is in the `<style>` section

## 🔧 Troubleshooting

### "No face detected"
- Use a photo with a clear, frontal face
- Make sure face is well-lit
- Try a different photo

### "Template not found"
- Make sure you have .mp4 files in `static/template_videos/`
- Restart the server after adding templates

### Videos processing slowly
- Templates should be 10 seconds or less
- Use 720p or lower resolution templates
- Close other apps to free up CPU

### Can't access from iPhone
- Make sure iPhone and computer are on same WiFi
- Check your computer's firewall settings
- Try disabling VPN if active
- Verify the IP address is correct

### FFmpeg errors
- Make sure FFmpeg is installed: `ffmpeg -version`
- On macOS, you might need to allow it in Security settings
- Try reinstalling FFmpeg

## 📁 Project Structure

```
face-swap-app/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
│
├── templates/
│   └── index.html             # Web interface (mobile-optimized)
│
├── static/
│   ├── template_videos/       # Put your template .mp4 files here
│   ├── uploads/               # Temporary uploaded photos (auto-created)
│   └── output/                # Generated videos (auto-created)
│
└── temp/                      # Temporary processing files (auto-created)
```

## 🎯 Tips for Best Results

### Photo Tips:
- Use clear, well-lit photos
- Face should be looking at camera
- Avoid sunglasses (unless you want that effect)
- Higher resolution is better
- One face per photo (app uses first detected face)

### Template Tips:
- 5-10 seconds is ideal
- Person should keep face visible
- Simple backgrounds work better
- Good lighting essential
- 720p resolution is plenty

## 🛡️ Privacy & Data

- **All processing happens on your computer** - nothing sent to external servers
- **Photos are stored temporarily** in `static/uploads/`
- **You can delete generated videos** anytime from `static/output/`
- **To clear everything:**
  ```bash
  # Delete all uploads and outputs
  rm static/uploads/*
  rm static/output/*
  rm temp/*
  ```

## 🔒 Security Note

This app is designed for **personal use only**:
- No user authentication
- No input validation for production
- Not secured for public internet exposure
- **Do not deploy to public internet without security hardening**

Safe to use:
- ✅ On your home network
- ✅ For personal/family fun
- ✅ Shared with trusted friends on same WiFi

## 🚀 Advanced: Deploy to Internet (Optional)

Want to access from anywhere? Deploy to a free hosting service:

### Option 1: Railway (Recommended)
1. Sign up at [railway.app](https://railway.app)
2. Connect GitHub repository
3. Add FFmpeg buildpack
4. Deploy!

### Option 2: Render
1. Sign up at [render.com](https://render.com)
2. Create new Web Service
3. Connect repository
4. Add build command: `pip install -r requirements.txt`
5. Add start command: `python app.py`

**Note:** Free tiers might be slow for video processing.

## 🎉 Ideas for Fun

- **Birthday videos** - Put birthday person's face on dancing template
- **Holiday greetings** - Everyone's faces on holiday video
- **Family fun** - Mix and match family members' faces
- **Pet humor** - Try your pet's face (if face detection works!)
- **Throwback** - Use old photos for nostalgia

## 🐛 Known Limitations

- Face detection works best with frontal faces
- Face blending is simple (not deepfake quality)
- No face tracking (face stays in one position)
- One face per video
- Processing takes 10-30 seconds per video

These are features, not bugs! This is a simple, fun tool. 😄

## 📝 Future Improvements (Ideas)

- [ ] Multiple faces per video
- [ ] Better face blending/lighting adjustment
- [ ] Face tracking (face follows template person)
- [ ] Text overlays
- [ ] Background music options
- [ ] Batch processing (create multiple videos at once)
- [ ] Face position adjustment slider

## 🤝 Contributing

This is a personal project, but feel free to:
- Fork and modify for your own use
- Share improvements
- Create cool templates
- Have fun!

## 📄 License

Free for personal use. Have fun! 🎉

## ❓ Questions?

Common questions:

**Q: Why is my video quality lower than the template?**
A: We use fast encoding for speed. For better quality, edit line 147 in `app.py` and change `-crf 23` to `-crf 18`.

**Q: Can I use multiple faces in one video?**
A: Not yet! Currently supports one face per video.

**Q: Can I sell videos made with this?**
A: This is for personal fun only. Commercial use requires proper licensing.

**Q: Why doesn't it look like a real deepfake?**
A: This uses simple overlay for speed and simplicity. Real deepfakes require much more complex AI and processing power.

---

**Made with ❤️ for personal fun and learning**

Enjoy creating silly videos! 🎭🎉
