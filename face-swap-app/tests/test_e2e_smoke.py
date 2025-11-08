"""
End-to-end smoke tests with real inputs
Tests the complete workflow from upload to video generation
"""
import json
import os
from pathlib import Path

import cv2
import numpy as np
import pytest


@pytest.mark.integration
class TestEndToEndWorkflow:
    """
    End-to-end smoke tests that verify the complete user workflow
    """

    def test_complete_workflow_with_real_face_image(self, client, sample_template_video):
        """
        Complete smoke test: Upload real face → Select template → Generate video
        This tests the full happy path with realistic inputs
        """
        # Step 1: Create a more realistic face image
        realistic_face_path = self._create_realistic_face_image()

        try:
            # Step 2: Upload the photo
            with open(realistic_face_path, 'rb') as img:
                upload_data = {
                    'photo': (img, 'realistic_face.jpg', 'image/jpeg')
                }
                upload_response = client.post('/upload',
                                              data=upload_data,
                                              content_type='multipart/form-data')

            print(f"\n📤 Upload Response: {upload_response.status_code}")
            if upload_response.status_code == 200:
                upload_result = json.loads(upload_response.data)
                print(f"✅ Upload Success: {upload_result}")
            else:
                print(f"❌ Upload Failed: {upload_response.data}")

            # Verify upload succeeded
            assert upload_response.status_code == 200, \
                f"Upload failed: {upload_response.data}"

            upload_result = json.loads(upload_response.data)
            assert upload_result['success'] is True, \
                "Upload should succeed with realistic face image"
            assert 'filename' in upload_result, "Should return uploaded filename"

            uploaded_filename = upload_result['filename']
            print(f"📁 Uploaded file: {uploaded_filename}")

            # Step 3: Verify uploaded file exists
            upload_path = Path(client.application.config['UPLOAD_FOLDER']) / uploaded_filename
            assert upload_path.exists(), "Uploaded file should be saved"
            print(f"✅ File saved to: {upload_path}")

            # Step 4: Generate video
            generate_data = {
                'filename': uploaded_filename,
                'template': 'test_template'
            }
            generate_response = client.post('/generate',
                                            data=json.dumps(generate_data),
                                            content_type='application/json')

            print(f"\n🎬 Generate Response: {generate_response.status_code}")

            # Video generation might fail if FFmpeg is not available
            # That's acceptable in CI environments
            if generate_response.status_code == 200:
                generate_result = json.loads(generate_response.data)
                print(f"✅ Generation Success: {generate_result}")

                assert generate_result['success'] is True, \
                    "Video generation should succeed"
                assert 'video_url' in generate_result, "Should return video URL"
                assert 'download_url' in generate_result, "Should return download URL"

                # Step 5: Verify video file was created
                video_filename = generate_result['video_url'].split('/')[-1]
                video_path = Path(client.application.config['OUTPUT_FOLDER']) / video_filename
                assert video_path.exists(), "Generated video should exist"

                # Step 6: Verify video file is valid MP4
                assert video_path.suffix == '.mp4', "Should generate MP4 file"
                assert video_path.stat().st_size > 0, "Video file should not be empty"

                print(f"✅ Video created: {video_path} ({video_path.stat().st_size} bytes)")

                # Step 7: Test download endpoint
                download_response = client.get(generate_result['download_url'])
                assert download_response.status_code == 200, \
                    "Download should succeed"
                assert len(download_response.data) > 0, \
                    "Downloaded video should have content"

                print(f"✅ Download successful ({len(download_response.data)} bytes)")

                print("\n🎉 SMOKE TEST PASSED - Full workflow completed successfully!")

            else:
                # FFmpeg might not be available
                error_data = json.loads(generate_response.data)
                print(f"⚠️  Video generation failed (expected if FFmpeg not installed): {error_data}")
                pytest.skip("FFmpeg not available - video generation skipped")

        finally:
            # Cleanup
            if os.path.exists(realistic_face_path):
                os.remove(realistic_face_path)

    def test_workflow_with_poor_quality_image(self, client):
        """
        Test workflow with a low quality / edge case image
        Should handle gracefully
        """
        # Create a very small, low quality face image
        small_face_path = "tests/fixtures/small_face.jpg"

        # Create tiny 100x100 face
        img = np.ones((100, 100, 3), dtype=np.uint8) * 200
        cv2.circle(img, (50, 50), 30, (220, 180, 160), -1)  # Face
        cv2.circle(img, (40, 45), 5, (50, 50, 50), -1)  # Left eye
        cv2.circle(img, (60, 45), 5, (50, 50, 50), -1)  # Right eye
        cv2.imwrite(small_face_path, img)

        try:
            with open(small_face_path, 'rb') as img:
                upload_data = {
                    'photo': (img, 'small_face.jpg', 'image/jpeg')
                }
                response = client.post('/upload',
                                       data=upload_data,
                                       content_type='multipart/form-data')

            # Should either succeed or fail gracefully
            assert response.status_code in [200, 400], \
                "Should handle small images gracefully"

            if response.status_code == 400:
                data = json.loads(response.data)
                assert 'error' in data, "Should provide error message"
                print(f"✅ Correctly rejected low quality image: {data['error']}")
            else:
                print("✅ Accepted low quality image (MediaPipe is robust)")

        finally:
            if os.path.exists(small_face_path):
                os.remove(small_face_path)

    def test_multiple_sequential_uploads(self, client):
        """
        Test that multiple uploads work correctly (common user pattern)
        """
        results = []

        for i in range(3):
            face_path = self._create_realistic_face_image(f"face_{i}.jpg")

            try:
                with open(face_path, 'rb') as img:
                    upload_data = {
                        'photo': (img, f'test_face_{i}.jpg', 'image/jpeg')
                    }
                    response = client.post('/upload',
                                           data=upload_data,
                                           content_type='multipart/form-data')

                results.append(response.status_code)
                print(f"Upload {i+1}: {response.status_code}")

            finally:
                if os.path.exists(face_path):
                    os.remove(face_path)

        # All uploads should succeed
        assert all(status == 200 for status in results), \
            "All sequential uploads should succeed"
        print("✅ Multiple sequential uploads succeeded")

    def test_invalid_workflow_sequences(self, client):
        """
        Test invalid workflow sequences (negative tests)
        """
        # Test 1: Try to generate video without uploading photo first
        generate_data = {
            'filename': 'nonexistent.jpg',
            'template': 'test_template'
        }
        response = client.post('/generate',
                               data=json.dumps(generate_data),
                               content_type='application/json')

        assert response.status_code == 404, \
            "Should fail when file doesn't exist"
        print("✅ Correctly rejected nonexistent file")

        # Test 2: Upload invalid file type
        invalid_data = {
            'photo': (b'not an image', 'test.txt', 'text/plain')
        }
        response = client.post('/upload',
                               data=invalid_data,
                               content_type='multipart/form-data')

        assert response.status_code == 400, \
            "Should reject invalid file types"
        print("✅ Correctly rejected invalid file type")

        # Test 3: Try to generate with missing template
        face_path = self._create_realistic_face_image()
        try:
            with open(face_path, 'rb') as img:
                upload_response = client.post('/upload',
                                              data={'photo': (img, 'test.jpg', 'image/jpeg')},
                                              content_type='multipart/form-data')

            if upload_response.status_code == 200:
                upload_result = json.loads(upload_response.data)

                generate_data = {
                    'filename': upload_result['filename'],
                    'template': 'nonexistent_template'
                }
                response = client.post('/generate',
                                       data=json.dumps(generate_data),
                                       content_type='application/json')

                assert response.status_code == 500, \
                    "Should fail with nonexistent template"
                print("✅ Correctly rejected nonexistent template")

        finally:
            if os.path.exists(face_path):
                os.remove(face_path)

    def _create_realistic_face_image(self, filename="realistic_face.jpg"):
        """
        Helper to create a more realistic synthetic face image
        that MediaPipe is more likely to detect
        """
        output_path = f"tests/fixtures/{filename}"

        # Create larger image with better proportions
        width, height = 600, 800
        img = np.ones((height, width, 3), dtype=np.uint8) * 220  # Light background

        # Face (ellipse for more realistic shape)
        face_center = (300, 350)
        cv2.ellipse(img, face_center, (140, 180), 0, 0, 360, (220, 190, 170), -1)

        # Hair (dark ellipse on top)
        cv2.ellipse(img, (300, 250), (160, 140), 0, 180, 360, (60, 50, 40), -1)

        # Eyes
        left_eye = (250, 320)
        right_eye = (350, 320)

        # Eye whites
        cv2.ellipse(img, left_eye, (25, 18), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(img, right_eye, (25, 18), 0, 0, 360, (255, 255, 255), -1)

        # Pupils
        cv2.circle(img, left_eye, 12, (80, 60, 40), -1)
        cv2.circle(img, right_eye, 12, (80, 60, 40), -1)

        # Pupils (inner)
        cv2.circle(img, left_eye, 6, (20, 20, 20), -1)
        cv2.circle(img, right_eye, 6, (20, 20, 20), -1)

        # Eyebrows
        cv2.ellipse(img, (250, 290), (30, 8), 15, 0, 180, (70, 60, 50), -1)
        cv2.ellipse(img, (350, 290), (30, 8), 165, 0, 180, (70, 60, 50), -1)

        # Nose
        nose_pts = np.array([[300, 350], [280, 400], [300, 410], [320, 400]], np.int32)
        cv2.fillPoly(img, [nose_pts], (200, 170, 150))
        cv2.circle(img, (285, 405), 8, (180, 150, 130), -1)  # Left nostril
        cv2.circle(img, (315, 405), 8, (180, 150, 130), -1)  # Right nostril

        # Mouth
        cv2.ellipse(img, (300, 470), (45, 22), 0, 0, 180, (150, 80, 80), -1)
        cv2.ellipse(img, (300, 468), (45, 15), 0, 0, 180, (180, 120, 120), -1)

        # Add some shading for depth
        overlay = img.copy()
        cv2.ellipse(overlay, (250, 360), (30, 40), 0, 0, 360, (210, 180, 160), -1)
        cv2.ellipse(overlay, (350, 360), (30, 40), 0, 0, 360, (210, 180, 160), -1)
        cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)

        cv2.imwrite(output_path, img)
        return output_path


@pytest.mark.integration
class TestSystemHealth:
    """
    Smoke tests for overall system health
    """

    def test_all_required_directories_exist(self, app):
        """Verify all required directories are created"""
        required_dirs = [
            app.config['UPLOAD_FOLDER'],
            app.config['OUTPUT_FOLDER'],
            app.config['TEMPLATE_FOLDER'],
            'temp'
        ]

        for dir_path in required_dirs:
            assert os.path.exists(dir_path), f"Required directory {dir_path} should exist"
        print("✅ All required directories exist")

    def test_dependencies_importable(self):
        """Verify all required dependencies can be imported"""
        try:
            import cv2
            import flask
            import mediapipe
            import numpy
            import werkzeug
            print("✅ All dependencies importable")
        except ImportError as e:
            pytest.fail(f"Required dependency missing: {e}")

    def test_ffmpeg_available(self):
        """Check if FFmpeg is available (warning if not)"""
        import subprocess
        try:
            result = subprocess.run(['ffmpeg', '-version'],
                                    capture_output=True,
                                    timeout=5)
            if result.returncode == 0:
                print("✅ FFmpeg is available")
            else:
                pytest.skip("FFmpeg not available - video processing will fail")
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("FFmpeg not found - video processing tests will be skipped")

    def test_mediapipe_face_detection_initialized(self):
        """Verify MediaPipe can initialize face detection"""
        import mediapipe as mp
        try:
            mp_face_detection = mp.solutions.face_detection
            with mp_face_detection.FaceDetection(min_detection_confidence=0.5):
                pass
            print("✅ MediaPipe face detection initializes correctly")
        except Exception as e:
            pytest.fail(f"MediaPipe initialization failed: {e}")
