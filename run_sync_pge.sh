#!/bin/bash
# Helper script to run sync with pge conda environment

# Activate pge conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate pge

# Run the sync
python sync_outlook_caldav.py
