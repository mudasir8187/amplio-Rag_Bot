#!/usr/bin/env bash
set -e
apt-get update -y
apt-get install -y tesseract-ocr poppler-utils
pip install -r requirements.txt