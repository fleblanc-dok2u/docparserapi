from flask import Flask, request, jsonify, send_file,render_template,url_for
import os
import json
import mimetypes
import random
import string
import requests
import pandas as pd
import io


# Ensure we can import extractTable from the "py" folder
# from py.processDocument import get_document_layout
from py.processDocument import get_document_ocr,get_document_layout  # Assuming extractTable.py contains parse_document and extract_tables functions



# File paths
UPLOAD_FOLDER = "uploads"
OUTPUT_PATH = "static/data"


app = Flask(__name__)

def generate_random_string(n, chars=string.ascii_letters + string.digits):
    # Generate a random string with N characters.
    return ''.join(random.choices(string.digits, k=n))

@app.route("/")
def home():
    """Serve the HTML page."""
    return render_template("index.html")

@app.route("/get_layout", methods=["POST"])
def get_layout():
    """
    1. Accepts a file upload (PDF, image, etc.).
    2. Calls parse_document() to extract structured data.
    3. Returns the extracted CSV file to the client.
    """
    try:
        rndstring = "0000" #generate_random_string(5)

        # Step 1: Check if a file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        # Create user folder with specific id
        user_path = OUTPUT_PATH+"/"+rndstring+"/"
        os.makedirs(user_path, exist_ok=True)  # Ensure output folder exists

        # Upload files ans save it on the server
        uploaded_file = request.files["file"]
        file_path = os.path.join(user_path, uploaded_file.filename)
        uploaded_file.save(file_path)

        # Step 2: Get file metadata
        file_size = os.path.getsize(file_path)  # Get file size in bytes
        mime_type = mimetypes.guess_type(file_path)[0]  # Detect MIME type


        # Step 3: Parse document using Google Document AI
        document_data = get_document_layout(file_path)

        # Step 4: Save extracted data to JSON
        filename_without_extension = os.path.splitext(uploaded_file.filename)[0]
        output_json_path = OUTPUT_PATH+"/"+filename_without_extension+".json"
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(document_data, json_file, indent=4, ensure_ascii=False)
            
        # Step 6: Generate a download link for the CSV
        download_url = request.host_url + output_json_path

        # Step 7: Return JSON response with file details and download link
        response_data = {
            "file_name": uploaded_file.filename,
            "file_size_bytes": file_size,
            "mime_type": mime_type,
            "download_url": download_url
        }

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/get_ocr", methods=["POST"])
def get_ocr():
    """
    1. Accepts a file upload (PDF, image, etc.).
    2. Calls parse_document() to extract structured data.
    3. Returns the extracted CSV file to the client.
    """
    try:
        rndstring = "0000" #generate_random_string(5)

        # Step 1: Check if a file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        # Create user folder with specific id
        user_path = OUTPUT_PATH+"/"+rndstring+"/"
        os.makedirs(user_path, exist_ok=True)  # Ensure output folder exists

        # Upload files ans save it on the server
        uploaded_file = request.files["file"]
        file_path = os.path.join(user_path, uploaded_file.filename)
        uploaded_file.save(file_path)

        # Step 2: Get file metadata
        file_size = os.path.getsize(file_path)  # Get file size in bytes
        mime_type = mimetypes.guess_type(file_path)[0]  # Detect MIME type

        # Step 3: Parse document using Google Document AI
        response_data = get_document_ocr(file_path,user_path)

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  # Run on port 8080
  