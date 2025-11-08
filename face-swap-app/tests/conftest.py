"""
Test configuration and fixtures for face-swap-app
"""
import os
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config.update({
        "TESTING": True,
        "UPLOAD_FOLDER": "tests/fixtures/uploads",
        "OUTPUT_FOLDER": "tests/fixtures/output",
        "TEMPLATE_FOLDER": "tests/fixtures/templates"
    })

    # Create test directories
    os.makedirs(flask_app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(flask_app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(flask_app.config['TEMPLATE_FOLDER'], exist_ok=True)
    os.makedirs('temp', exist_ok=True)

    yield flask_app

    # Cleanup after tests
    # Note: Keeping test fixtures for inspection, but could clean up here


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_face_image():
    """
    Create a simple synthetic face image for testing
    Returns path to the image file
    """
    # Create a simple face-like image using OpenCV
    # This is a basic representation - MediaPipe should detect it

    img_path = "tests/fixtures/test_face.jpg"

    # Create a 400x400 image with a face-like structure
    img = np.ones((400, 400, 3), dtype=np.uint8) * 200  # Light gray background

    # Draw a circular face
    cv2.circle(img, (200, 200), 100, (220, 180, 160), -1)  # Skin tone

    # Draw two eyes
    cv2.circle(img, (170, 180), 15, (50, 50, 50), -1)  # Left eye
    cv2.circle(img, (230, 180), 15, (50, 50, 50), -1)  # Right eye

    # Draw nose
    pts = np.array([[200, 200], [190, 230], [210, 230]], np.int32)
    cv2.fillPoly(img, [pts], (200, 160, 140))

    # Draw mouth
    cv2.ellipse(img, (200, 250), (30, 15), 0, 0, 180, (150, 50, 50), -1)

    # Save image
    cv2.imwrite(img_path, img)

    return img_path


@pytest.fixture
def sample_no_face_image():
    """
    Create an image without a face for testing
    Returns path to the image file
    """
    img_path = "tests/fixtures/test_no_face.jpg"

    # Create a simple landscape image
    img = np.ones((400, 400, 3), dtype=np.uint8)

    # Blue sky
    img[:200] = [200, 150, 100]

    # Green grass
    img[200:] = [100, 180, 100]

    # Yellow sun
    cv2.circle(img, (100, 100), 40, (100, 200, 250), -1)

    cv2.imwrite(img_path, img)

    return img_path


@pytest.fixture
def sample_template_video():
    """
    Create a simple test video template
    Returns path to the video file
    """
    video_path = "tests/fixtures/templates/test_template.mp4"

    # Video properties
    fps = 10
    duration = 2  # seconds
    width, height = 640, 480

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))

    # Generate frames (2 seconds at 10 fps = 20 frames)
    for i in range(fps * duration):
        # Create a frame with a moving circle
        frame = np.ones((height, width, 3), dtype=np.uint8) * 100

        # Moving circle (represents where a face would be)
        x = 320
        y = 240 + int(20 * np.sin(i * 0.3))  # Slight vertical motion
        cv2.circle(frame, (x, y), 80, (200, 200, 200), -1)

        out.write(frame)

    out.release()

    return video_path


@pytest.fixture
def cleanup_test_files():
    """Cleanup fixture that runs after tests"""
    yield

    # Cleanup test uploads and outputs
    import shutil
    test_dirs = [
        'tests/fixtures/uploads',
        'tests/fixtures/output'
    ]

    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
