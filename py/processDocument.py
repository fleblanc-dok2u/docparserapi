import json
import json
import os
from google.protobuf.json_format import MessageToDict
from PIL import Image
import base64
import io
import mimetypes
import re
import pymupdf  # PyMuPDF
from datetime import datetime

from py.saveLayout import  generate_html_with_bboxes # Assuming extractTable.py contains parse_document and extract_tables functions
from google.cloud import documentai_v1beta3 as documentai

from typing import Optional, Sequence

# Set your Google Cloud project details
PROJECT_ID = "224181475341"
LOCATION = "us"  # Change based on your region (us, eu, asia)
LAYOUT_PROCESSOR_ID = "4ca554ec865b513f"  # Get from Document AI Console
OCR_PROCESSOR_ID = "3aa9a60af5830b28"  # Get from Document AI Console

# https://us-documentai.googleapis.com/v1/projects/224181475341/locations/us/processors/3aa9a60af5830b28:process
# https://us-documentai.googleapis.com/v1/projects/224181475341/locations/us/processors/4ca554ec865b513f:process
# Authenticate using service account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../dok2u-sante-26dbdd75e5d7.json"


def split_pdf(input_pdf, output_folder, max_pages=10):
    """Splits a large PDF into smaller PDFs with max_pages per chunk."""
    doc = pymupdf.open(input_pdf)
    chunck_list = []
    for i in range(0, len(doc), max_pages):
        new_doc = pymupdf.open()
        for j in range(i, min(i + max_pages, len(doc))):
            new_doc.insert_pdf(doc, from_page=j, to_page=j)
        
        output_path = f"{output_folder}/split_{i+1}.pdf"
        new_doc.save(output_path)
        chunck_list.append(output_path)
        print(f"Saved: {output_path}")
    return chunck_list

def get_pdf_page_count(pdf_path):
    """Returns the total number of pages in a PDF file."""
    doc = pymupdf.open(pdf_path)  # Open the PDF
    return len(doc)  # Get total number of pages


def get_pdf_ocr(file_path,output_path):
    
    # Initialize Document AI client
    client = documentai.DocumentProcessorServiceClient()
    mime_type="application/pdf"
    
    #Split file in chunks of 10 pages max
    folder_name = os.path.dirname(file_path)
    chunck_list = split_pdf(file_path,folder_name,10)
    
    structured_data = {"blocks": [], "tables": [], "images": []}
    global_page_offset = 0
    for chunk_index, chunk_file in enumerate(chunck_list):
        # Read file as binary
        with open(chunk_file, "rb") as file:
            file_content = file.read()

        # Create a raw document request
        raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)

        # Configure layout request
        processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{OCR_PROCESSOR_ID}"
        request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
        
        # Send request
        chunk_result  = client.process_document(request=request)

        # Parse response
        document = chunk_result.document  # Document AI output
    
        # Extract text, bounding boxes, and page numbers
        new_block_dict = extract_text_blocks_and_tables_and_images(document,global_page_offset,output_path)
        
        # Update blockid and page offset to maintain global numbering
        global_page_offset += get_pdf_page_count(chunk_file)
        
        for key in ["blocks", "tables", "images"]:
            structured_data[key].extend(new_block_dict[key])

   
    #Save layout
    # json_path = os.path.join(output_path, f"layout.json")
    # file_list.append(json_path)  
    # with open(json_path, "w", encoding="utf-8") as json_file:
    #     json.dump(blocks_list, json_file, indent=4, ensure_ascii=False)
    return structured_data

def get_document_ocr(file_path,output_path):
    
    # Initialize Document AI client
    client = documentai.DocumentProcessorServiceClient()
    
    # Determine MIME type based on file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        raise ValueError(f"Unsupported file type for file: {file_path}")
    
    
    # Read the file content
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()
    except FileNotFoundError as e:
        raise FileNotFoundError(f"File not found: {file_path}") from e

    # Create a raw document request
    raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)

    # Configure layout request
    processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{OCR_PROCESSOR_ID}"
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
        
    # Send request
    result  = client.process_document(request=request)

    # Parse response
    document = result.document  # Document AI output
    
    # Extract text, bounding boxes, and page numbers
    structured_data = extract_text_blocks_and_tables_and_images(document,0,output_path)

    #Save layout
    # json_path = os.path.join(output_path, f"layout.json")
    # with open(json_path, "w", encoding="utf-8") as json_file:
    #     json.dump(structured_data, json_file, indent=4, ensure_ascii=False)
    return structured_data

 

# Function to extract text, blocks, and tables from the OCR response
def extract_text_blocks_and_tables_and_images(document, page_offset, output_folder):
    """
    Extracts structured text (blocks) and tables from the OCR response.
    Returns a dictionary containing 'blocks' and 'tables'.
    """
    text = document.text  # Full text of the document
    structured_data = {"blocks": [], "tables": [], "images": []}

    for page in document.pages:
        page_number = page.page_number+page_offset

        # Extract text blocks
        for block in page.blocks:
            block_text = ""
            for segment in block.layout.text_anchor.text_segments:
                block_text += text[int(segment.start_index):int(segment.end_index)]
            
            structured_data["blocks"].append({
                "page": page_number,
                "text": block_text,
                "bounding_box": [(v.x, v.y) for v in block.layout.bounding_poly.vertices]
            })

        # Extract tables
        for table in page.tables:
            table_data = []
            for row in table.body_rows:
                row_data = []
                for cell in row.cells:
                    cell_text = ""
                    for segment in cell.layout.text_anchor.text_segments:
                        cell_text += text[int(segment.start_index):int(segment.end_index)]
                    row_data.append(cell_text)
                table_data.append(row_data)

            structured_data["tables"].append({
                "page": page_number,
                "table": table_data,
                "bounding_box": [(v.x, v.y) for v in table.layout.bounding_poly.vertices]
            })
            
        if page.image.content:
            image_path = save_base64_image(page.image.content, output_folder, f"page_{page_number}",page.image.mime_type)
            structured_data["images"].append({
                "page": page_number,
                "path": image_path,
                "width": page.image.width,
                "height": page.image.height,
                "mim_type": page.image.mime_type
            })
            
    return structured_data


def save_base64_image(image_base64, output_folder, fileprefix, mime_type):
    """
    Decodes and saves a base64 image from Document AI response, handling multiple image formats.

    Parameters:
    - image_base64 (str): Base64 encoded image content.
    - output_folder (str): Directory to save extracted images.
    - filename (str): Filename prefix for saving.
    - format_hint (str, optional): Suggested format (e.g., "jpeg", "png", "tiff").

    Returns:
    - str: Path to the saved image, or None if an error occurs.
    """
    try:

        # Load image using PIL (Auto-detect format)
        try:
            image = Image.open(io.BytesIO(image_base64))
            print(f"Image format detected: {image.format}")
        except Exception as e:
            print(f"PIL cannot open image: {e}")



        # Define correct file extensions
        mime_map = {
            "image/jpeg": ("JPEG", "jpg"),
            "image/png": ("PNG", "png"),
            "image/tiff": ("TIFF", "tiff"),
            "image/bmp": ("BMP", "bmp"),
            "image/gif": ("GIF", "gif"),
            "image/webp": ("WEBP", "webp")
        }

        # Get the correct extension, default to PNG if unknown
        format_name, extension = mime_map.get(mime_type.lower(), ("PNG", "png"))  # Default to PNG

        # Get current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Save image with detected format
        image_filename =  f"{fileprefix}_{timestamp}.{extension}"
        image_path = os.path.join(output_folder, image_filename)
        image.save(image_path, format_name.upper())
        print(f"Saving Image: {image_filename}")

        return image_path

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

