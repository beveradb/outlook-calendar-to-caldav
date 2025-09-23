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

def create_dummy_image_with_text(text: str, filepath: str):
    # Create a simple image with the given text
    img = Image.new('RGB', (400, 100), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    # Try to use a common font, or fallback to default
    try:
        fnt = ImageFont.truetype("Arial.ttf", 20)
    except IOError:
        fnt = ImageFont.load_default()
    d.text((10,10), text, fill=(0,0,0), font=fnt)
    img.save(filepath)

def test_process_image_with_ocr_success():
    expected_text = "Hello World!"
    create_dummy_image_with_text(expected_text, TEST_IMAGE_FILE)
    
    extracted_text = process_image_with_ocr(TEST_IMAGE_FILE)
    
    # pytesseract often adds newlines or spaces, so we strip and check for containment
    assert expected_text in extracted_text.strip()

def test_process_image_with_ocr_file_not_found():
    with pytest.raises(FileNotFoundError, match=f"Image file not found at {TEST_IMAGE_FILE}"):
        process_image_with_ocr(TEST_IMAGE_FILE)
