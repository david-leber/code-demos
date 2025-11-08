# ⚡ Quick Start Guide - Face Swap App

Get up and running in 5 minutes!

## Step 1: Install Prerequisites (One Time)

### Install Python
```bash
python --version  # Should be 3.9 or higher
```
If not installed: Download from https://www.python.org/downloads/

### Install FFmpeg
```bash
ffmpeg -version  # Check if installed
```

**Not installed?**

**Mac:**
```bash
brew install ffmpeg
```

**Windows:** Download from https://ffmpeg.org or use:
```bash
choco install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

## Step 2: Set Up the App (First Time)

```bash
# 1. Go to app directory
cd face-swap-app

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate  # Windows

# 4. Install dependencies
pip install -r requirements.txt
```

## Step 3: Add Template Videos

You need at least ONE template video to get started.

**Option A: Record with your phone** (Recommended!)
1. Open camera app
2. Record a 5-second video of yourself waving
3. Transfer to computer (AirDrop/email/cable)
4. Save as `static/template_videos/wave.mp4`

**Option B: Download free stock video**
1. Go to https://www.pexels.com/videos/
2. Search "person waving"
3. Download a short clip
4. Save as `static/template_videos/wave.mp4`

## Step 4: Run the App

```bash
python app.py
```

You'll see:
```
* Running on http://0.0.0.0:5000
```

## Step 5: Open in Browser

**On same computer:**
```
http://localhost:5000
```

**On iPhone (same WiFi):**

1. Find your computer's IP address:
   - **Mac**: System Settings → Network (e.g., 192.168.1.100)
   - **Windows**: CMD → `ipconfig` → IPv4 Address
   - **Linux**: Terminal → `hostname -I`

2. On iPhone, open Safari:
   ```
   http://YOUR_IP:5000
   ```
   Example: `http://192.168.1.100:5000`

3. Bookmark it for easy access!

## Step 6: Create Your First Video! 🎉

1. **Upload a photo** - Tap the upload area, take a selfie
2. **Pick your template** - Tap the video template
3. **Generate** - Tap "Generate Video" button
4. **Wait 10-30 seconds** - Your video is being created
5. **Watch & Share!** - Video appears, download or share

Done! 🎭

## Troubleshooting

**"No templates available"**
→ Add .mp4 files to `static/template_videos/` folder and restart

**"No face detected"**
→ Use a clearer photo with face looking at camera

**Can't access from iPhone**
→ Make sure both devices are on same WiFi network

**Video processing fails**
→ Make sure FFmpeg is installed: `ffmpeg -version`

## Next Steps

- Add more templates to `static/template_videos/`
- Customize face size/position in `app.py`
- Share with friends and family!
- Have fun creating silly videos!

## Full Documentation

See `README.md` for complete details, customization options, and advanced features.

---

**Total setup time: 5-10 minutes**
**Fun level: Unlimited!** 🎉
