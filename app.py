from flask import Flask, request, jsonify, render_template,send_from_directory
import os
import json
import mimetypes
import random
import string
import requests
import pandas as pd
import uuid


# Ensure we can import extractTable from the "py" folder
# from py.processDocument import get_document_layout
from py.processDocument import get_document_ocr,get_pdf_ocr  # Assuming extractTable.py contains parse_document and extract_tables functions



# File paths
OUTPUT_PATH = "static/data"
UPLOAD_FOLDER = "static/image"

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

def create_app():
    
    ####################################################
    # Startup configuration
    ####################################################   
    #For debug set GOOGLE_APPLICATION_CREDENTIALS to pathto\credentials.json in environment variables 

    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../dok2u-sante-26dbdd75e5d7.json"
 
    
    app = Flask(__name__)


    @app.route("/")
    def home():
        """Serve the HTML page."""
        # return render_template("editor.html")
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
            
            code = request.form.get('sessionid')  # this is your 6-digit code

            # Create user folder with specific id
            user_path = OUTPUT_PATH+"/"+code+"/"
            os.makedirs(user_path, exist_ok=True)  # Ensure output folder exists
            
            # Clear folder
            clear_folder(user_path)
            
            # Upload files ans save it on the server
            uploaded_file = request.files["file"]
            file_path = os.path.join(user_path, uploaded_file.filename)
            uploaded_file.save(file_path)
            
            # Determine MIME type based on file extension
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                raise ValueError(f"Unsupported file type for file: {file_path}")
            
            # Parse document using Google Document AI
            if(mime_type=="application/pdf"):
                response_data = get_pdf_ocr(file_path,user_path)
            else:
                response_data = get_document_ocr(file_path,user_path)

            return jsonify(response_data)
        
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    @app.route('/uploadFile', methods=['POST'])
    def upload_file():
        if 'image' not in request.files:
            return jsonify({'success': 0, 'message': 'No image part'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': 0, 'message': 'No selected file'}), 400

        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        return jsonify({
            'success': 1,
            'file': {
                'url': f'/{UPLOAD_FOLDER}/{filename}'
            }
        })

    @app.route('/fetchUrl', methods=['POST'])
    def fetch_url():
        data = request.get_json()
        image_url = data.get('url')

        if not image_url:
            return jsonify({'success': 0, 'message': 'No URL provided'}), 400

        try:
            response = requests.get(image_url)
            response.raise_for_status()

            ext = os.path.splitext(image_url.split('?')[0])[1] or '.jpg'
            filename = f"{uuid.uuid4()}{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)

            with open(filepath, 'wb') as f:
                f.write(response.content)

            return jsonify({
                'success': 1,
                'file': {
                    'url': f'/uploads/{filename}'
                }
            })
        except Exception as e:
            return jsonify({'success': 0, 'message': str(e)}), 500

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)    
    
    return app

# Start  web server
if __name__ == '__main__':
        
    #Use projectid = podolive-prod if compiling for master and podolive-dev in development
    #Create app
    app = create_app()
    
    #Production server
    app.run(host='0.0.0.0', port=8080, debug=True)  # Run on port 8080
