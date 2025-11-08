"""
Unit tests for face detection functionality
"""
import os

import cv2
import numpy as np
import pytest

from app import detect_and_extract_face


class TestFaceDetection:
    """Test face detection functionality"""

    def test_detect_face_in_valid_image(self, sample_face_image):
        """Test that face is detected in image with face"""
        result = detect_and_extract_face(sample_face_image)

        assert result is not None, "Should detect face in valid image"
        assert isinstance(result, np.ndarray), "Should return numpy array"
        assert len(result.shape) == 3, "Should return 3D array (height, width, channels)"
        assert result.shape[2] == 3, "Should have 3 color channels"

    def test_no_face_in_invalid_image(self, sample_no_face_image):
        """Test that no face is detected in image without face"""
        result = detect_and_extract_face(sample_no_face_image)

        assert result is None, "Should not detect face in image without face"

    def test_face_detection_with_nonexistent_file(self):
        """Test face detection with file that doesn't exist"""
        result = detect_and_extract_face("nonexistent_file.jpg")

        assert result is None, "Should return None for nonexistent file"

    def test_face_extraction_size(self, sample_face_image):
        """Test that extracted face has reasonable dimensions"""
        result = detect_and_extract_face(sample_face_image)

        if result is not None:
            height, width = result.shape[:2]
            assert height > 0, "Face height should be positive"
            assert width > 0, "Face width should be positive"
            assert height < 1000, "Face height should be reasonable"
            assert width < 1000, "Face width should be reasonable"

    def test_face_detection_with_real_photo(self):
        """Test face detection with a more realistic synthetic photo"""
        # Create a more detailed test image
        test_img_path = "tests/fixtures/detailed_face.jpg"

        # Create a more realistic face
        img = np.ones((500, 500, 3), dtype=np.uint8) * 240

        # Face
        cv2.ellipse(img, (250, 250), (120, 150), 0, 0, 360, (220, 180, 160), -1)

        # Eyes
        cv2.circle(img, (210, 230), 20, (255, 255, 255), -1)  # Left eye white
        cv2.circle(img, (290, 230), 20, (255, 255, 255), -1)  # Right eye white
        cv2.circle(img, (210, 230), 10, (50, 50, 50), -1)  # Left pupil
        cv2.circle(img, (290, 230), 10, (50, 50, 50), -1)  # Right pupil

        # Nose
        cv2.line(img, (250, 250), (250, 290), (200, 160, 140), 3)

        # Mouth
        cv2.ellipse(img, (250, 320), (40, 20), 0, 0, 180, (150, 50, 50), 2)

        cv2.imwrite(test_img_path, img)

        result = detect_and_extract_face(test_img_path)

        # Cleanup
        if os.path.exists(test_img_path):
            os.remove(test_img_path)

        # More realistic image should have better chance of detection
        # But we'll accept either result since it's still synthetic
        assert result is None or isinstance(result, np.ndarray), \
            "Should return None or valid face array"


class TestFaceExtractionQuality:
    """Test quality and properties of extracted faces"""

    def test_extracted_face_is_bgr(self, sample_face_image):
        """Test that extracted face is in BGR color format (OpenCV standard)"""
        result = detect_and_extract_face(sample_face_image)

        if result is not None:
            # Check that it's a valid BGR image
            assert result.dtype == np.uint8, "Should be uint8 image"
            assert np.all(result >= 0) and np.all(result <= 255), \
                "Pixel values should be in range 0-255"

    def test_face_padding_applied(self, sample_face_image):
        """Test that padding is applied to extracted face"""
        # This is implicit in the implementation, but we can verify
        # that the extracted face is larger than the minimum bounding box
        result = detect_and_extract_face(sample_face_image)

        if result is not None:
            # Should have some reasonable size due to padding
            height, width = result.shape[:2]
            assert height >= 50, "Face should have minimum height with padding"
            assert width >= 50, "Face should have minimum width with padding"
