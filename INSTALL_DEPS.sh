#!/bin/bash
# Install dependencies for calendar-sync in pge conda environment

echo "Installing Python dependencies in pge conda environment..."
conda activate pge
pip install -r requirements.txt

echo "✅ Dependencies installed!"
echo ""
echo "To test the improved OCR, run:"
echo "  python sync_outlook_caldav.py"
