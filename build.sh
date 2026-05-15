#!/usr/bin/env bash
set -e
sudo apt-get update -y
sudo apt-get install -y tesseract-ocr poppler-utils
pip install -r requirements.txt