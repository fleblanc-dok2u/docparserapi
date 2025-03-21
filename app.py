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
from py.extractTables import extract_tables,get_document_layout  # Assuming extractTable.py contains parse_document and extract_tables functions



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
    # return render_template("index.html")
    return render_template("inaf.html")

@app.route("/get_tables", methods=["POST"])
def get_tables():
    """
    1. Accepts a file upload (PDF, image, etc.).
    2. Calls parse_document() to extract structured data.
    3. Calls extract_tables() to extract required table values.
    4. Returns the extracted CSV file to the client.
    """
    try:
        rndstring = generate_random_string(5)

        # Step 1: Check if a file was uploaded
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        uploaded_file = request.files["file"]
        file_path = os.path.join(UPLOAD_FOLDER, rndstring+"_"+uploaded_file.filename)
        uploaded_file.save(file_path)

        # Step 2: Get file metadata
        file_size = os.path.getsize(file_path)  # Get file size in bytes
        mime_type = mimetypes.guess_type(file_path)[0]  # Detect MIME type

        # Step 3: Parse document using Google Document AI
        document_data = get_document_layout(file_path)

        # Step 4: Save extracted data to JSON
        output_json_path = OUTPUT_PATH+"/output_"+rndstring+".json"
        with open(output_json_path, "w", encoding="utf-8") as json_file:
            json.dump(document_data, json_file, indent=4, ensure_ascii=False)

        # Step 5: Extract tables from JSON and save to CSV
        output_csv_path = OUTPUT_PATH+"/output_"+rndstring+".csv"
        extract_tables(output_json_path,  output_csv_path)

        # Step 6: Generate a download link for the CSV
        download_url = request.host_url + output_csv_path

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
    
@app.route('/download_all', methods=['POST'])
def download_all():
    """
    Merges multiple CSV files from given URLs and returns a single CSV to the client.
    """
    try:
        rndstring = generate_random_string(5)
        # Get the list of URLs from the request
        data = request.json
        urls = data.get("urls", [])

        if not urls:
            return jsonify({"error": "No CSV URLs provided"}), 400

        merged_data = []

        for i, file_path in enumerate(urls):
            try:
                response = requests.get(file_path)
                response.raise_for_status()

                # Read CSV with `;` delimiter
                df = pd.read_csv(io.StringIO(response.text), delimiter=";", encoding="utf-8")

                # Convert "Tag" column to be headers, with "Valeur" as row data
                df = df.set_index("Tag").T

                # Store data
                merged_data.append(df)
                    
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")
        
        if not merged_data:
            return jsonify({"error": "No valid CSV files found"}), 400

        # Merge all CSV data line by line
        merged_df = pd.concat(merged_data, ignore_index=True)
        
        # Keep the first three columns as input order, others sorted
        base_columns = merged_df.columns[:4].tolist()
        remaining_columns = sorted([col for col in merged_df.columns[4:]])
        column_order = base_columns + remaining_columns
        merged_df = merged_df[column_order]
        
        # Save merged CSV
        output_csv_path = OUTPUT_PATH+"/merged_output_"+rndstring+".csv"
        merged_df.to_csv(output_csv_path, index=False, sep=";", encoding="utf-8-sig")

        # Return merged CSV to client
        return send_file(output_csv_path, as_attachment=True, download_name="merged_output.csv"),200

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
    
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
        user_path = OUTPUT_PATH+rndstring+"/"
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
    
# @app.route("/get_ocr", methods=["POST"])
# def get_ocr():
#     """
#     1. Accepts a file upload (PDF, image, etc.).
#     2. Calls parse_document() to extract structured data.
#     3. Returns the extracted CSV file to the client.
#     """
#     try:
#         rndstring = "0000" #generate_random_string(5)

#         # Step 1: Check if a file was uploaded
#         if "file" not in request.files:
#             return jsonify({"error": "No file uploaded"}), 400

#         # Create user folder with specific id
#         user_path = OUTPUT_PATH+rndstring+"/"
#         os.makedirs(user_path, exist_ok=True)  # Ensure output folder exists

#         # Upload files ans save it on the server
#         uploaded_file = request.files["file"]
#         file_path = os.path.join(user_path, uploaded_file.filename)
#         uploaded_file.save(file_path)

#         # Step 2: Get file metadata
#         file_size = os.path.getsize(file_path)  # Get file size in bytes
#         mime_type = mimetypes.guess_type(file_path)[0]  # Detect MIME type

#         # Step 3: Parse document using Google Document AI
#         file_list = processDocument.get_document_ocr(file_path,user_path)

#         # Step 4: Return JSON response with file details and download link
#         response_data = {
#             "file_name": uploaded_file.filename,
#             "file_size_bytes": file_size,
#             "mime_type": mime_type,
#             "download_file_list": file_list
#         }

#         return jsonify(response_data)
    
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)  # Run on port 8080
  