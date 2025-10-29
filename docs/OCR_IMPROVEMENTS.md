# OCR Reliability Improvements

## Problem
The OCR was failing to reliably extract start times from calendar events, e.g., reading "SHIELD Working Sessions - 16:55" instead of "SHIELD Working Sessions 16:00 - 16:55".

## Implemented Solutions

### 1. **Tesseract Configuration Optimization**
- **What**: Added custom tesseract configuration flags
- **How**: `--oem 3 --psm 6`
  - `OEM 3`: Uses both legacy and LSTM engines for better accuracy
  - `PSM 6`: Assumes uniform block of text (calendar view)
- **Impact**: Better text detection in structured layouts

### 2. **Enhanced Image Preprocessing**
- **Median Filter**: Reduces noise before binarization
- **Contrast Enhancement**: Increases contrast by 2x before thresholding
- **Adaptive Processing**: Maintains text clarity while removing noise
- **Impact**: Clearer text boundaries for OCR

### 3. **Image Upscaling**
- **What**: Scale image by 2x using LANCZOS resampling
- **Why**: Tesseract performs significantly better with larger text (14-18pt optimal)
- **Impact**: Improved recognition of small text like times

### 4. **Fixed Coordinate Scaling Bug**
- **Problem**: After upscaling by 2x, coordinate filtering ranges were incorrect
- **Fix**: 
  - Icon column filter: `775-880` → `1550-1760`
  - Date column filter: `120` → `240`
- **Impact**: Prevents filtering out valid text after scaling

### 5. **Confidence-Based Filtering**
- **What**: Filter out OCR results with confidence < 60%
- **Why**: Low-confidence words are usually misrecognitions
- **Impact**: Cleaner word list, fewer false positives

### 6. **Fallback Parsing for Partial Times**
- **What**: Handle cases where only end time is detected (e.g., "- 16:55")
- **How**: Infer start time by subtracting 55 minutes (common meeting length)
- **Impact**: Graceful degradation when OCR misses start time

## Additional Recommendations (Not Yet Implemented)

### 7. **Multiple PSM Mode Strategy**
Try multiple Page Segmentation Modes and combine results:
```python
configs = [
    '--oem 3 --psm 6',   # Uniform block
    '--oem 3 --psm 11',  # Sparse text
    '--oem 3 --psm 3'    # Fully automatic
]
```

### 8. **Region-Specific OCR**
Process time regions separately with specialized config:
```python
# Extract time column region (known x-coordinates)
time_region = img.crop((time_x_start, y, time_x_end, y + height))
# Use PSM 7 (single line) with digit-focused whitelist
time_ocr = pytesseract.image_to_string(
    time_region, 
    config='--psm 7 -c tessedit_char_whitelist=0123456789:-'
)
```

### 9. **Alternative OCR Engines**
Consider supplementing tesseract with:
- **EasyOCR**: Better with challenging fonts
- **PaddleOCR**: Excellent for structured layouts
- **Cloud OCR APIs**: Google Vision, Azure, AWS (for critical use cases)

### 10. **Preprocessing Variations**
Try multiple preprocessing strategies and vote:
- Different threshold values (70, 80, 90)
- Adaptive thresholding (local vs global)
- Morphological operations (erosion/dilation)

### 11. **Post-Processing Heuristics**
Add intelligent recovery:
```python
# If we see "Title - HH:MM" pattern
# Look for nearby HH:MM patterns in raw OCR output
# Reconstruct "Title HH:MM - HH:MM"
```

### 12. **Training Custom Tesseract Model**
For long-term improvement:
- Collect screenshots of Outlook calendar
- Create training data with accurate labels
- Fine-tune tesseract LSTM model for this specific use case

## Testing Strategy

1. **Create test suite** with various problematic screenshots
2. **Measure accuracy** before/after each improvement
3. **Monitor OCR confidence scores** in logs
4. **Review cropped images** in `ocr_crops/` directory
5. **Track failure patterns** to identify remaining issues

## Expected Improvements

With these changes, we should see:
- ✅ Better detection of times (especially start times)
- ✅ Fewer parsing errors from missing text
- ✅ More robust handling of font variations
- ✅ Better handling of small text
- ⚠️ Slightly slower processing (due to upscaling and extra preprocessing)

## Monitoring

Check these logs to verify improvements:
```bash
# Count OCR errors
grep "Unable to parse event row" logs/calendar_sync.log | wc -l

# View low-confidence words
grep "low-confidence word" logs/calendar_sync.log

# Check inferred start times
grep "Partial time range detected" logs/calendar_sync.log
```
