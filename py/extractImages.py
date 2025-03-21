
import fitz

import os
from google.cloud import documentai_v1beta3 as documentai
from google.protobuf.json_format import MessageToDict
from PIL import Image

# Google Cloud credentials (Ensure GOOGLE_APPLICATION_CREDENTIALS is set)
# Set your Google Cloud project details
PROJECT_ID = "373815688414"
LOCATION = "us"  # Change based on your region (us, eu, asia)
PROCESSOR_ID = "c07a954868a2e329"  # Get from Document AI Console
CREDENTIALS_PATH = "vosker-b01eff5a44f3.json"  # JSON key file


# Ensure credentials are set (or set manually)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH


def extract_images_from_pdf(pdf_path, output_folder):
    doc = fitz.open(pdf_path)  # Open the PDF file
    os.makedirs(output_folder, exist_ok=True)  # Create output folder if not exists

    for page_number, page in enumerate(doc, start=1):
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]  # Image reference
            
            base_image = doc.extract_image(xref)  # Extract image
            image_bytes = base_image["image"]  # Get image bytes
            image_ext = base_image["ext"]  # Get image extension (e.g., 'png', 'jpeg')

            image_filename = f"page_{page_number}_img_{img_index}.{image_ext}"
            image_path = os.path.join(output_folder, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)  # Save image file

            print(f"Extracted: {image_filename}")
            
def extract_images_positions(pdf_path):
    doc = fitz.open(pdf_path)  # Open the PDF
    
    for page_num, page in enumerate(doc, start=1):
        images = page.get_images(full=True)  # Get all images in the page
        
        for img_index, img in enumerate(images, start=1):
            xref = img[7]  # Image reference
            bbox = page.get_image_bbox(xref)  # Get bounding box of image
            
            print(f"Page {page_num} - Image {img_index}:")
            print(f"  - Bounding Box: {bbox}")
            print(f"  - XREF: {xref}\n")
            
# Example usage
# pdf_path = "./data/Information_à_l_usager_Thérapie_par_pression_négative_VF_sept_2024.pdf"
# output_folder = "extracted_images"
# extract_images(pdf_path, output_folder)
# extract_images_positions(pdf_path)

