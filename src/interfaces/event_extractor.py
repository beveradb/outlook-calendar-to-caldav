"""
Abstract interface for event extraction services.
Follows the Dependency Inversion Principle.
"""
from abc import ABC, abstractmethod
from typing import List
from src.models.calendar_data import ParsedEvent


class IEventExtractor(ABC):
    """Interface for extracting calendar events from various sources"""
    
    @abstractmethod
    def extract_events(self, image_path: str) -> List[ParsedEvent]:
        """
        Extract calendar events from an image.
        
        Args:
            image_path: Path to the screenshot/image file
            
        Returns:
            List of parsed calendar events
        """
        pass


class OCREventExtractor(IEventExtractor):
    """Extract events using OCR (Tesseract)"""
    
    def extract_events(self, image_path: str) -> List[ParsedEvent]:
        """Extract events using OCR"""
        from src.ocr_processor import process_image_with_ocr
        return process_image_with_ocr(image_path)


class GeminiEventExtractor(IEventExtractor):
    """Extract events using Gemini Vision API"""
    
    def __init__(self, api_key: str):
        """
        Initialize the Gemini event extractor.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
    
    def extract_events(self, image_path: str) -> List[ParsedEvent]:
        """Extract events using Gemini Vision API"""
        from src.gemini_extractor import extract_events_with_gemini
        return extract_events_with_gemini(image_path, self.api_key)


class BedrockEventExtractor(IEventExtractor):
    """Extract events using Claude Vision on AWS Bedrock"""

    def __init__(self, model_id: str = None, region: str = None):
        from src.bedrock_extractor import DEFAULT_MODEL_ID, DEFAULT_REGION
        self.model_id = model_id or DEFAULT_MODEL_ID
        self.region = region or DEFAULT_REGION

    def extract_events(self, image_path: str) -> List[ParsedEvent]:
        """Extract events using Claude on Bedrock"""
        from src.bedrock_extractor import extract_events_with_bedrock
        return extract_events_with_bedrock(image_path, self.model_id, self.region)


class FallbackEventExtractor(IEventExtractor):
    """
    Try Gemini first, fall back to OCR if it fails.
    Decorator pattern for fallback behavior.
    """
    
    def __init__(self, primary: IEventExtractor, fallback: IEventExtractor):
        """
        Initialize with primary and fallback extractors.
        
        Args:
            primary: Primary extraction method to try first
            fallback: Fallback extraction method if primary fails
        """
        self.primary = primary
        self.fallback = fallback
    
    def extract_events(self, image_path: str) -> List[ParsedEvent]:
        """Try primary extractor, fall back to secondary on failure"""
        try:
            return self.primary.extract_events(image_path)
        except Exception:
            return self.fallback.extract_events(image_path)
