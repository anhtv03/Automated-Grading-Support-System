import io
import json
import os
import re
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
import google.generativeai as genai
from PIL import Image
from fastapi import File, UploadFile
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document as LangchainDocument

from app.constants.file_type import FileType

EXTRACT_PDF_API_KEYS = os.getenv("EXTRACT_PDF_KEYS", "").split(",")

async def is_word_or_excel(file: UploadFile = File(...)) -> str:
    file_extension = Path(file.filename).suffix.lower()
    if file_extension in {'.docx', '.doc'}:
        return FileType.Word
    elif file_extension in {'.xlsx', '.xls'}:
        return FileType.Excel
    return None


@staticmethod
def clean_text(text):
    """Clean text by removing noise and normalizing whitespace."""
    text = re.sub(r'(\w+)-\s*(\w+)', r'\1\2', text)  # Combine the split words.
    text = re.sub(r'[^\w\s\.\!\?]', '', text)  # Remove special characters
    text = re.sub(r'\s+', ' ', text.strip())  # Normalize whitespace
    text = re.sub(r'(?<![\.\!\?])\n', ' ', text)  # Remove \n not after . ! ?
    text = re.sub(r'\n{2,}', '\n', text).strip()  # Normalize multiple newlines
    return text


@staticmethod
def filter_header_footer(ocr_text, previous_text=None):
    """Filter out header and footer based on keywords and previous page content."""
    lines = ocr_text.split('\n')
    if len(lines) > 2:
        if any("Section" in line or "Chapter" in line or "Copyright" in line for line in lines[:2]):
            lines = lines[2:]
        if any("Copyright" in line for line in lines[-2:]):
            lines = lines[:-2]
    if previous_text:
        common_start = os.path.commonprefix([ocr_text, previous_text])
        if len(common_start) > 20:
            lines = lines[len(common_start.split('\n')):]
        common_end = os.path.commonprefix([ocr_text[::-1], previous_text[::-1]])
        if len(common_end) > 10:
            lines = lines[:-len(common_end.split('\n')[::-1])]
    return '\n'.join(lines)


def extract_text_from_json(ocr_result):
    """Extract text from various JSON structures returned by Gemini."""
    if not isinstance(ocr_result, dict):
        return ""
    text_parts = []

    def recursive_extract(obj):
        if isinstance(obj, str):
            text_parts.append(obj)
        elif isinstance(obj, dict):
            for value in obj.values():
                recursive_extract(value)
        elif isinstance(obj, list):
            for item in obj:
                recursive_extract(item)

    recursive_extract(ocr_result)
    return " ".join(text_parts).strip()


@staticmethod
def read_document_pdf(pdf_path: str, api_keys: List[str] = EXTRACT_PDF_API_KEYS) -> List[LangchainDocument]:
    """Reads a PDF document, extracts text with PyPDFLoader, and uses Gemini for OCR on pages with potential image content."""
    if not api_keys:
        raise ValueError("No API keys provided")

    print(f"Processing PDF file: {pdf_path}")
    all_pages_langchain_documents = []
    previous_text = None

    doc = fitz.open(pdf_path)
    total_pages_in_pdf = len(doc)

    loader = PyPDFLoader(pdf_path)
    pypdf_documents = loader.load()

    if len(pypdf_documents) < total_pages_in_pdf:
        for _ in range(total_pages_in_pdf - len(pypdf_documents)):
            pypdf_documents.append(LangchainDocument(page_content="", metadata={}))

    for i in range(total_pages_in_pdf):
        print(f"Processing page {i + 1}/{total_pages_in_pdf}")
        page = doc[i]
        page_height = page.rect.height
        clip = fitz.Rect(0, 100, page.rect.width, page_height - 100)  # remove header/footer
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=clip)
        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        page_content = pypdf_documents[i].page_content
        page_metadata = pypdf_documents[i].metadata

        ocr_text = None
        last_exception = None
        for index, api_key in enumerate(api_keys):
            try:
                genai.configure(api_key=api_key)
                gemini_model = genai.GenerativeModel("gemini-1.5-flash")

                response = gemini_model.generate_content(
                    [
                        "Extract all text from this image and return it in a structured JSON format with a single field 'page_content' containing all the text.",
                        {"mime_type": "image/png", "data": img_data}
                    ],
                    generation_config={
                        "response_mime_type": "application/json"
                    }
                )
                ocr_result = json.loads(response.text)
                if isinstance(ocr_result, dict) and "page_content" in ocr_result:
                    ocr_text = ocr_result["page_content"]
                else:
                    ocr_text = extract_text_from_json(ocr_result)
                    print(f"Unexpected OCR response format on page {i + 1}, extracted text: {ocr_text[:50]}...")
                break

            except Exception as e:
                print(f"Unexpected error with API key {index + 1} on page {i + 1}: {e}")
                last_exception = e
                if index == len(api_keys) - 1:
                    print(f"All API keys exhausted for page {i + 1}")
                    ocr_text = None
                continue

        if ocr_text and len(ocr_text) > 20:
            page_content = page_content + "\n" + ocr_text if page_content else ocr_text
        elif last_exception:
            print(f"Skipping OCR for page {i + 1} due to failure: {last_exception}")

        page_content = filter_header_footer(page_content, previous_text)
        previous_text = page_content
        page_content = clean_text(page_content)
        page_metadata.update({'source': pdf_path, 'page': i, 'page_label': str(i + 1)})

        all_pages_langchain_documents.append(LangchainDocument(page_content=page_content, metadata=page_metadata))

    doc.close()
    return all_pages_langchain_documents


@staticmethod
def read_document_docx(docx_path: str) -> list[LangchainDocument]:
    """Reads a DOCX document, extracts text with UnstructuredWordDocumentLoader """
    print(f"Processing DOCX file: {docx_path}")
    loader = UnstructuredWordDocumentLoader(docx_path)
    documents = loader.load()
    for i, doc in enumerate(documents):
        doc.metadata.update({'source': docx_path, 'page': 0,
                             'page_label': f"Part {i + 1}"})
    return documents
