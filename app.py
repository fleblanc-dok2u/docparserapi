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
OUTPUT_PATH = "static/data"


app = Flask(__name__)

# def generate_random_string(n, chars=string.ascii_letters + string.digits):
#     # Generate a random string with N characters.
#     return ''.join(random.choices(string.digits, k=n))

@app.route("/")
def home():
    """Serve the HTML page."""
    return render_template("index.html")


@app.route("/get_ocr", methods=["POST"])
def get_ocr():
    """
    1. Accepts a file upload (PDF, image, etc.).
    2. Calls parse_document() to extract structured data.
    3. Returns the extracted json file to the client.
    """
    try:

        # Step 1: Check if a file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        code = request.form.get('code')  # this is your 6-digit code

        # Create user folder with specific id
        user_path = OUTPUT_PATH+"/"+code+"/"
        os.makedirs(user_path, exist_ok=True)  # Ensure output folder exists

        # Upload files ans save it on the server
        uploaded_file = request.files["file"]
        file_path = os.path.join(user_path, uploaded_file.filename)
        uploaded_file.save(file_path)

        # Parse document using Google Document AI
        response_data = get_document_ocr(file_path,user_path)

        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  # Run on port 8080
  