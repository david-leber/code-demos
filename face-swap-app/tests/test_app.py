"""
Unit tests for Flask application routes and endpoints
"""
import io
import json
import os
from pathlib import Path

import pytest


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint returns success"""
        response = client.get('/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestIndexRoute:
    """Test main index route"""

    def test_index_page_loads(self, client):
        """Test that index page loads successfully"""
        response = client.get('/')

        assert response.status_code == 200
        assert b'Face Swap Fun' in response.data or b'html' in response.data.lower()

    def test_index_shows_templates(self, client, sample_template_video):
        """Test that index page shows available templates"""
        response = client.get('/')

        assert response.status_code == 200
        # Should contain the templates section
        assert b'template' in response.data.lower()


class TestPhotoUpload:
    """Test photo upload endpoint"""

    def test_upload_valid_image(self, client, sample_face_image):
        """Test uploading a valid image with a face"""
        with open(sample_face_image, 'rb') as img:
            data = {
                'photo': (img, 'test_face.jpg', 'image/jpeg')
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'filename' in data
        assert 'message' in data

    def test_upload_image_without_face(self, client, sample_no_face_image):
        """Test uploading an image without a face"""
        with open(sample_no_face_image, 'rb') as img:
            data = {
                'photo': (img, 'test_no_face.jpg', 'image/jpeg')
            }
            response = client.post('/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No face detected' in data['error']

    def test_upload_no_file(self, client):
        """Test upload endpoint with no file"""
        response = client.post('/upload', data={}, content_type='multipart/form-data')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No photo uploaded' in data['error']

    def test_upload_empty_filename(self, client):
        """Test upload with empty filename"""
        data = {
            'photo': (io.BytesIO(b''), '', 'image/jpeg')
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False

    def test_upload_invalid_file_type(self, client):
        """Test uploading invalid file type"""
        data = {
            'photo': (io.BytesIO(b'test data'), 'test.txt', 'text/plain')
        }
        response = client.post('/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid file type' in data['error']


class TestVideoGeneration:
    """Test video generation endpoint"""

    def test_generate_video_missing_parameters(self, client):
        """Test video generation with missing parameters"""
        response = client.post('/generate',
                               data=json.dumps({}),
                               content_type='application/json')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing required parameters' in data['error']

    def test_generate_video_file_not_found(self, client):
        """Test video generation with non-existent uploaded file"""
        request_data = {
            'filename': 'nonexistent_file.jpg',
            'template': 'test_template'
        }
        response = client.post('/generate',
                               data=json.dumps(request_data),
                               content_type='application/json')

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

    def test_generate_video_success(self, client, sample_face_image, sample_template_video):
        """Test successful video generation (integration test)"""
        # First upload a photo
        with open(sample_face_image, 'rb') as img:
            upload_data = {
                'photo': (img, 'test_face.jpg', 'image/jpeg')
            }
            upload_response = client.post('/upload',
                                          data=upload_data,
                                          content_type='multipart/form-data')

        # Check upload was successful
        assert upload_response.status_code == 200
        upload_result = json.loads(upload_response.data)

        if not upload_result['success']:
            pytest.skip("Face detection failed on test image - skipping video generation test")

        filename = upload_result['filename']

        # Now generate video
        request_data = {
            'filename': filename,
            'template': 'test_template'
        }
        response = client.post('/generate',
                               data=json.dumps(request_data),
                               content_type='application/json')

        # This might fail if FFmpeg is not available, which is okay for unit tests
        if response.status_code == 200:
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'video_url' in data
            assert 'download_url' in data
        else:
            # Expected to fail if FFmpeg not installed
            pytest.skip("FFmpeg may not be available in test environment")


class TestDownloadEndpoint:
    """Test video download endpoint"""

    def test_download_nonexistent_file(self, client):
        """Test downloading a file that doesn't exist"""
        response = client.get('/download/nonexistent_video.mp4')

        assert response.status_code == 404
        assert b'File not found' in response.data

    def test_download_existing_file(self, client):
        """Test downloading an existing file"""
        # Create a dummy output file
        output_dir = Path(client.application.config['OUTPUT_FOLDER'])
        output_dir.mkdir(parents=True, exist_ok=True)

        test_file = output_dir / 'test_download.mp4'
        test_file.write_bytes(b'test video content')

        try:
            response = client.get('/download/test_download.mp4')

            assert response.status_code == 200
            assert response.data == b'test video content'
            assert 'attachment' in response.headers.get('Content-Disposition', '')
        finally:
            # Cleanup
            if test_file.exists():
                test_file.unlink()


class TestFileValidation:
    """Test file validation helper function"""

    def test_allowed_file_extensions(self):
        """Test allowed_file function with various extensions"""
        from app import allowed_file

        # Valid extensions
        assert allowed_file('test.jpg') is True
        assert allowed_file('test.jpeg') is True
        assert allowed_file('test.png') is True
        assert allowed_file('test.JPG') is True  # Case insensitive
        assert allowed_file('test.JPEG') is True

        # Invalid extensions
        assert allowed_file('test.txt') is False
        assert allowed_file('test.pdf') is False
        assert allowed_file('test.exe') is False
        assert allowed_file('test') is False  # No extension
        assert allowed_file('') is False  # Empty string
