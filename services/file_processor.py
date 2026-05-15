import os
import uuid
from typing import List, Dict, Optional
import pypdf
import docx
import pandas as pd
import markdown
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter

# OCR Imports
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

if os.name == 'nt':  # Windows
    POPPLER_PATH = r'Release-24.08.0-0\poppler-24.08.0\Library\bin'
    TESSERACT_PATH = r'Tesseract-OCR\tesseract.exe'
else:
    POPPLER_PATH = None
    TESSERACT_PATH = None

import subprocess
result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
print("Tesseract location:", result.stdout.strip())
result2 = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
print("Tesseract version:", result2.stdout.strip()) 

# Configure pytesseract to use the specified Tesseract executable
if TESSERACT_PATH and os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    print("Warning: Tesseract executable not found at specified path or path not set. Please update TESSERACT_PATH in the script.")


def _load_txt(file_path: str) -> str:
    """Loads text content from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading TXT file {file_path}: {e}")
        return ""

def _load_pdf(file_path: str) -> str:
    """Loads text content from a PDF file, with OCR fallback for image-based PDFs."""
    text_from_pypdf = ""
    total_pages = 0

    try:
        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            total_pages = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text_from_pypdf += page_text + "\n"

    except Exception as e:
        print(f"Error during standard PDF text extraction for {file_path}: {e}.")

    print(f"Attempting OCR for {file_path}...")
    ocr_text = ""
    try:
        # Use the configured POPPLER_PATH. If None, pdf2image will look in PATH.
        # Ensure poppler_path is correctly set for your local environment.
        images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        for i, img in enumerate(images):
            try:
                # pytesseract.image_to_string will now use the configured tesseract_cmd
                page_ocr_text = pytesseract.image_to_string(img, lang='eng')
                ocr_text += f"\n\n--- Page {i+1} (OCR) ---\n{page_ocr_text}"
            except Exception as ocr_e:
                print(f"Error during OCR on page {i+1} of {file_path}: {ocr_e}")
        
        if ocr_text:
            print(f"Successfully extracted text using OCR for {file_path}.")
            # Combine pypdf extracted text with OCR text
            return text_from_pypdf + "\n\n" + ocr_text
        else:
            print(f"OCR also failed to extract significant text from {file_path}.")
            return text_from_pypdf # Return whatever pypdf extracted, even if sparse
    except Exception as final_e:
        print(f"Critical error: Could not process PDF {file_path} with OCR: {final_e}")
        return text_from_pypdf # Return whatever pypdf extracted, even if sparse
    

def _load_docx(file_path: str) -> str:
    """Loads text content from a DOCX file."""
    text = ""
    try:
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error loading DOCX file {file_path}: {e}")
        return ""

def _load_csv(file_path: str) -> str:
    """Loads text content from a CSV file, converting rows to text."""
    text = ""
    try:
        df = pd.read_csv(file_path)
        text = df.to_string(index=False)
        return text
    except Exception as e:
        print(f"Error loading CSV file {file_path}: {e}")
        return ""

def _load_md(file_path: str) -> str:
    """Loads text content from a Markdown file, converting to plain text."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        html = markdown.markdown(md_content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text()
    except Exception as e:
        print(f"Error loading Markdown file {file_path}: {e}")
        return ""

def load_document(file_path: str) -> str:
    """Loads text content from a supported file type."""
    _, file_extension = os.path.splitext(file_path.lower())
    
    if file_extension == '.txt':
        return _load_txt(file_path)
    elif file_extension == '.pdf':
        return _load_pdf(file_path)
    elif file_extension == '.docx':
        return _load_docx(file_path)
    elif file_extension == '.csv':
        return _load_csv(file_path)
    elif file_extension == '.md':
        return _load_md(file_path)
    else:
        print(f"Unsupported file type: {file_extension}")
        return ""

def chunk_text(text: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> List[str]:
    """Splits text into chunks using RecursiveCharacterTextSplitter."""
    if not text:
        return []
        
    # Assuming config.DEFAULT_CHUNK_SIZE and config.DEFAULT_CHUNK_OVERLAP are defined elsewhere
    # For demonstration, using arbitrary values if config is not available
    _chunk_size = chunk_size if chunk_size is not None else 1000 # Example default
    _chunk_overlap = chunk_overlap if chunk_overlap is not None else 200 # Example default

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=_chunk_size,
        chunk_overlap=_chunk_overlap,
        length_function=len,
        add_start_index=False,
    )
    
    chunks = text_splitter.split_text(text)
    return chunks

def process_file(file_path: str, actual_filename: str, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None) -> Dict:
    """Loads, chunks a file and assigns a unique ID."""
    print(f"Processing file: {file_path}")
    document_text = load_document(file_path)
    if not document_text:
        print(f"Failed to load text from {file_path}")
        return None

    chunks = chunk_text(document_text, chunk_size, chunk_overlap)
    if not chunks:
        print(f"No text chunks generated for {file_path}")
        return None
        
    document_id = str(uuid.uuid4())
    print(f"Generated {len(chunks)} chunks for document ID: {document_id}")

    return {
        "document_id": document_id,
        "chunks": chunks,
        "original_filename": actual_filename
    }



