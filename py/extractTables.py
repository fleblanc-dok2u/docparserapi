


import json
import re
import pandas as pd

from google.cloud import documentai_v1beta3 as documentai
import os
from google.protobuf.json_format import MessageToDict

TAGS_TO_EXTRACT = [
    "Cholestérol total", "HDL", "LDL", "Triglycérides", "Glucose à jeun",
    "Créatinine", "TriUréeglycérides", "Sodium", "Potassium", "Chlorures",
    "TSH", "GB", "GR", "Hb", "Ht", "Plaq", "VGM", "TGMH", "CGMH", "DVE", "VPM",
    "Neutrophiles", "Lymphocytes", "Monocytes", "Éosinophiles", "Basophiles",
    "Anticoagulant", "TCA", "TQ (INR)"
]
# Set your Google Cloud project details
PROJECT_ID = "933649852593"
LOCATION = "us"  # Change based on your region (us, eu, asia)
LAYOUT_PROCESSOR_ID = "65dc4d39e0995700"  # Get from Document AI Console

# https://us-documentai.googleapis.com/v1/projects/933649852593/locations/us/processors/65dc4d39e0995700:process

# # Authenticate using service account
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/dboulanger.CIMMI/Documents/Credentials/docparser-454014-667f8842ade2.json"

def get_document_layout(file_path):
    

    # Initialize Document AI client
    client = documentai.DocumentProcessorServiceClient()

    # Read file as binary
    with open(file_path, "rb") as file:
        file_content = file.read()

    # Create a raw document request

    raw_document = documentai.RawDocument(content=file_content, mime_type="application/pdf")

    # Configure layout request
    processor_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{LAYOUT_PROCESSOR_ID}"
    request = documentai.ProcessRequest(name=processor_name, raw_document=raw_document)
    
    # Send request
    result = client.process_document(request=request)

    # Parse response
    document = result.document
    blocks_list = [MessageToDict(block._pb) for block in document.document_layout.blocks]

    # Extract all block attributes
    # print("Document Layout Blocks")
    # for block in document.document_layout.blocks:
    #     print(block)
   
    return blocks_list

def remove_letters(text):
    return re.sub(r"[^\d,.]", "", text)  # Keep only digits (0-9), commas, and points

def extract_tables(json_file_path, csv_file_path):
        

    # Charger le fichier JSON
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

  
    # Extraire les valeurs qui suivent chaque tag
    extracted_data = []
    
    extracted_data.append(["Dossier", extract_first_block(json_file_path,"Dossier")])
    extracted_data.append(["Enregistré le", extract_first_block(json_file_path,"Enregistré le")])
    extracted_data.append(["Prélevé le", extract_first_block(json_file_path,"Prélevé le")])
    extracted_data.append(["Imprimé le", extract_first_block(json_file_path,"Imprimé le")])
    
    for block in data:
        if "tableBlock" in block:
            for row in block["tableBlock"].get("bodyRows", []):
                row_texts = []
                for cell in row.get("cells", []):
                    cell_texts = [
                        text_block["textBlock"]["text"]
                        for text_block in cell.get("blocks", [])
                        if "textBlock" in text_block and "text" in text_block["textBlock"]
                    ]
                    row_texts.extend(cell_texts)

                # Rechercher les tags et leur valeur suivante
                for i, text in enumerate(row_texts):
                    for tag in TAGS_TO_EXTRACT:
                        if text.strip() == tag and i + 1 < len(row_texts):
                            extracted_data.append([tag, remove_letters(row_texts[i + 1])])

                            
    # Convertir les données extraites en DataFrame
    df = pd.DataFrame(extracted_data, columns=["Tag", "Valeur"])

    # Sauvegarder en fichier CSV avec encodage UTF-8-SIG et séparateur `;`
    df.to_csv(csv_file_path, index=False, encoding="utf-8-sig", sep=";")

    print(f"Extraction terminée. Le fichier CSV est sauvegardé sous : {csv_file_path}")
 
def extract_first_block(json_file_path,block_name):
    """
    Extracts the first Dossier ID from text blocks containing 'Dossier' in output.json.
    """
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Iterate through text blocks to find "Dossier" and extract the first ID
    for block in data:
        if "textBlock" in block and "text" in block["textBlock"]:
            text = block["textBlock"]["text"]
            match = re.search(block_name+r"\s+(\S+)", text)  # Extract the word after "block_name"
            if match:
                return match.group(1)  # Return only the first occurrence

    return None  # Return None if no match is found
   
