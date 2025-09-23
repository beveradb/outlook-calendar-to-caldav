import pytest
import os
from PIL import Image, ImageDraw, ImageFont
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.ocr_processor import process_image_with_ocr

# Define a temporary image file path for testing
TEST_IMAGE_FILE = "test_ocr_image.png"

@pytest.fixture(autouse=True)
def cleanup_test_image_file():
    # Ensure the test image file is removed before and after each test
    if os.path.exists(TEST_IMAGE_FILE):
        os.remove(TEST_IMAGE_FILE)
    yield
    if os.path.exists(TEST_IMAGE_FILE):
        os.remove(TEST_IMAGE_FILE)

def test_process_image_with_ocr_file_not_found():
    with pytest.raises(FileNotFoundError, match=f"Image file not found at {TEST_IMAGE_FILE}"):
        process_image_with_ocr(TEST_IMAGE_FILE)
