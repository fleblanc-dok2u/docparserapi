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

from py.saveLayout import  generate_html_with_bboxes # Assuming extractTable.py contains parse_document and extract_tables functions


from typing import Optional, Sequence

# Set your Google Cloud project details
PROJECT_ID = "373815688414"
LOCATION = "us"  # Change based on your region (us, eu, asia)
LAYOUT_PROCESSOR_ID = "c07a954868a2e329"  # Get from Document AI Console
OCR_PROCESSOR_ID = "49cd9e89ceca3557"  # Get from Document AI Console
CREDENTIALS_PATH = "vosker-b01eff5a44f3.json"  # JSON key file

# Authenticate using service account
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

def convert_image_to_pdf(image_path):
    """Convert an image (JPG, PNG) to a single-page PDF."""
    pdf_path = image_path.rsplit(".", 1)[0] + ".pdf"  # Convert to PDF filename
    image = Image.open(image_path)  # Open image
    image.convert("RGB").save(pdf_path)  # Save as PDF
    return pdf_path

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


def adjust_blockid_and_pages(blocks, block_offset, page_offset):
    
    stack = blocks[:]  # Initialize stack with the top-level blocks
    max_block_id=0;
    while stack:
        block = stack.pop()  # Get the last element in stack (LIFO)
        block["blockId"] = str(int(block["blockId"]) + block_offset)
        block["pageSpan"]["pageStart"] += page_offset
        block["pageSpan"]["pageEnd"] += page_offset
        max_block_id = max(max_block_id,int(block["blockId"]))
            
        # If the block contains sub-blocks, process them recursively
        text_block = block.get("textBlock", {})
        if "blocks" in text_block:
            stack.extend(reversed(text_block["blocks"]))  # Reverse to maintain order

        # If the block is inside a table, iterate over table blocks
        if "tableBlock" in block:
            for row in block["tableBlock"].get("bodyRows", []):
                for cell in row.get("cells", []):
                    stack.extend(reversed(cell.get("blocks", [])))
                    
    return max_block_id

def save_all_images_in_pdf(file_path,output_path):
    #Save all images   
    file_list=[]
    doc = pymupdf.open(file_path)  # Open the PDF file
    for page_number, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]  # Image reference
                
            base_image = doc.extract_image(xref)  # Extract image
            image_bytes = base_image["image"]  # Get image bytes
            image_ext = base_image["ext"]  # Get image extension (e.g., 'png', 'jpeg')

            image_filename = f"page_{page_number}_img_{img_index}.{image_ext}"
            image_path = os.path.join(output_path, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)  # Save image file

            file_list.append(image_path)
            print(f"Extracted: {image_filename}")   
    return file_list

def get_document_layout(file_path,output_path):
    
    file_list = []

    # Initialize Document AI client
    client = documentai.DocumentProcessorServiceClient()
    mime_type="application/pdf"
    
    #Split file in chunks of 10 pages max
    folder_name = os.path.dirname(file_path)
    chunck_list = split_pdf(file_path,folder_name,10)
    
    blocks_list = []
    global_page_offset = 0
    global_block_offset= 0
    for chunk_index, chunk_file in enumerate(chunck_list):
        # Read file as binary
        with open(chunk_file, "rb") as file:
            file_content = file.read()

        # Create a raw document request
        raw_document = documentai.RawDocument(content=file_content, mime_type=mime_type)

        # Configure layout request
        processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{LAYOUT_PROCESSOR_ID}"
        request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
        
        # Send request
        chunk_result  = client.process_document(request=request)

        # Parse response
        layout_document = chunk_result.document
        new_block_list = [MessageToDict(block._pb) for block in layout_document.document_layout.blocks]

        # Update blockid and page offset to maintain global numbering
        global_block_offset = adjust_blockid_and_pages(new_block_list,global_block_offset,global_page_offset)
        global_page_offset += get_pdf_page_count(chunk_file)
        blocks_list.append(new_block_list)
   
    #Save layout
    json_path = os.path.join(output_path, f"layout.json")
    file_list.append(json_path)  
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(blocks_list, json_file, indent=4, ensure_ascii=False)
     
    #Save all images. Note it cannot extract Vector-based images 
    file_list += save_all_images_in_pdf(file_path,output_path)  
             
    return file_list

def get_document_ocr(file_path,output_path):
    
    file_list = []

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
    
    file_list = []
    # Extract text, bounding boxes, and page numbers
    structured_data = extract_text_blocks_and_tables(document,output_path)
    #Save layout
    json_path = os.path.join(output_path, f"layout.json")
    with open(json_path, "w", encoding="utf-8") as json_file:
        json.dump(structured_data, json_file, indent=4, ensure_ascii=False)

    # Extract images
    image_paths = save_extracted_images(document, output_path)

    html_path = os.path.join(output_path, f"output.html")
    # saveLayout.generate_html_from_structure(structured_data, image_paths, html_path)
    generate_html_with_bboxes(structured_data, image_paths[0], html_path)
    
    return file_list

# Function to extract text, blocks, and tables from the OCR response
def extract_text_blocks_and_tables(document, output_folder):
    """
    Extracts structured text (blocks) and tables from the OCR response.
    Returns a dictionary containing 'blocks' and 'tables'.
    """
    text = document.text  # Full text of the document
    structured_data = {"blocks": [], "tables": []}

    for page in document.pages:
        page_number = page.page_number

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

    return structured_data


# Function to save extracted images from Document AI output
def save_extracted_images(document, output_folder):
    """
    Extracts and saves all images from the Document AI OCR response.

    Parameters:
    - document (dict): The JSON response from Document AI.
    - output_folder (str): Directory to save extracted images.

    Returns:
    - list: Paths of saved images.
    """
    extracted_images = []
    for page_index, page in enumerate(document.pages, start=1):
        if page.image.content:
            image_path = save_base64_image(page.image.content, output_folder, f"page_{page_index}",page.image.mime_type)
            extracted_images.append(image_path)
    return extracted_images

def save_base64_image(image_base64, output_folder, filename, mime_type):
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

        # Save image with detected format
        image_filename =  f"{filename}.{extension}"
        image_path = os.path.join(output_folder, image_filename)
        image.save(image_path, format_name.upper())
        print(f"Saving Image: {image_filename}")

        return image_filename

    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

