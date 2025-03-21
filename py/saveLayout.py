import os
import json
from PIL import Image, ImageFont, ImageDraw

def get_image_size(image_path):
    """ Returns the width and height of an image. """
    with Image.open(image_path) as img:
        return img.width, img.height
    
def get_fitting_font_size(text, max_width, initial_font_size=200, min_font_size=10):
    """
    Adjusts the font size so that each line of text fits within the given max_width.

    Parameters:
    - text (str): The text to be displayed.
    - max_width (int): The maximum allowed width for each line.
    - initial_font_size (int): Starting font size.
    - min_font_size (int): Minimum allowed font size.

    Returns:
    - int: The best-fitting font size.
    """
    try:
        font_path = "/static/font/Roboto/static/Roboto-Bold.ttf"  # Adjust for your system
        font_size = initial_font_size

        # Split text into individual lines
        lines = text.split("\n")

        while font_size > min_font_size:
            font = ImageFont.truetype(font_path, font_size)

            # Check if all lines fit within max_width
            fits = all(font.getlength(line) <= max_width for line in lines)

            if fits:
                return font_size  # All lines fit within width, return this size
            
            font_size -= 1  # Reduce font size and try again

        return min_font_size  # If no fit found, return minimum size
    except Exception:
        return min_font_size  # Default if font rendering fails

def generate_html_from_structure(structured_data, image_paths, output_html="output.html"):
    """
    Generates an HTML document using extracted text structure and images.
    
    Parameters:
    - structured_data (dict): Contains 'blocks' (text) and 'tables' (structured data).
    - image_paths (list): Paths to the extracted background images.
    - output_html (str): Path to save the generated HTML file.
    """
    html_template = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OCR Processed Document</title>
        <style>
            @font-face {
                font-family: 'MyCustomFont'; /* Give your font a name */
                src: url('/static/font/Roboto/static/Roboto-Bold.ttf') format('truetype'); /* Path to TTF */
                font-weight: normal;
                font-style: normal;
            }

            body {
                font-family: 'MyCustomFont', sans-serif;
                margin: 0;
                padding: 0;
            }
            .page {
                position: relative;
                margin: 20px auto;
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                border: 1px solid #ccc;
            }
            .text-block {
                position: absolute;
                background: rgba(255, 255, 255, 0.6);
                color: black;
                padding: 5px;
                font-weight: bold;
                overflow: hidden;
                word-wrap: break-word;
                text-align: left;
            }
            .table {
                position: absolute;
                border-collapse: collapse;
                background: rgba(255, 255, 255, 0.6);
            }
            .table td, .table th {
                border: 1px solid black;
                padding: 5px;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
    """

    for page_num, image_path in enumerate(image_paths, start=1):
        # Get page width and height dynamically from the image
        page_width, page_height = get_image_size(image_path)

        html_template += f'<div class="page" style="background-image: url(\'{image_path}\'); width: {page_width}px; height: {page_height}px;">\n'
        
        # Add Text Blocks (Positioned Over the Image)
        bbox_offset=15
        for block in structured_data.get("blocks", []):
            if block["page"] == page_num:
                bbox = block["bounding_box"]
                x = bbox[0][0]    # Top-left coordinates
                y = bbox[0][1]    # Top-left coordinates
                width = bbox[1][0] - x  # Width
                height = bbox[2][1] - y  # Height (bounding box height)

                # Process text: Ensure text ends with \n, then replace "\n" with "<br>"
                text_content = block["text"].strip()
                if not text_content.endswith("\n"):
                    text_content += "\n"  # Ensure new line at the end
                
                text_content = text_content.replace("\n", "<br>")

                # Count the number of lines
                num_lines = block["text"].count("\n") + 1  # At least 1 line

                # Adjust font size dynamically to fit bbox width
                font_size = get_fitting_font_size(block["text"],0.9*width)

                html_template += f'''
                <div class="text-block" style="
                    top: {y - bbox_offset}px; left: {x- bbox_offset}px; width: {width+ 2*bbox_offset}px; height: {height+ 2*bbox_offset}px;
                    font-size: {font_size}px; line-height: {font_size + 2}px;">
                    {text_content}
                </div>
                '''
        
        # Add Tables
        for table in structured_data.get("tables", []):
            if table["page"] == page_num:
                bbox = table["bounding_box"]
                x, y = bbox[0]  # Top-left coordinates

                html_template += f'<table class="table" style="top: {y}px; left: {x}px;">\n'
                for row in table["table"]:
                    html_template += "<tr>\n"
                    for cell in row:
                        html_template += f'<td>{cell}</td>'
                    html_template += "</tr>\n"
                html_template += "</table>\n"

        html_template += "</div>\n"  # End of page div

    html_template += "</body></html>"

    # Save the HTML file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"✅ HTML file generated: {output_html}")
 
def generate_html_with_bboxes(structured_data, image_path, output_html="output.html"):
    """
    Generates an HTML page displaying an image with bounding boxes.
    Shows tooltips with extracted text when hovering over a bounding box.
    
    Parameters:
    - structured_data (dict): Contains 'blocks' (text and bbox data).
    - image_path (str): Path to the background image.
    - output_html (str): Path to save the generated HTML file.
    """
    page_width, page_height = get_image_size(image_path)
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image with Bounding Boxes</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }}
            .container {{
                position: relative;
                display: inline-block;
            }}
            .image {{
                max-width: 100%;
                height: auto;
            }}
            .bbox {{
                position: absolute;
                border: 2px solid red;
                background: rgba(255, 0, 0, 0.2);
                cursor: pointer;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 5px;
                border-radius: 5px;
                display: none;
                font-size: 14px;
                max-width: 250px;
            }}
        </style>
    </head>
    <body>
    
        <h2>Image with Bounding Boxes</h2>
        <div class="container">
            <img id="backgroundImage" class="image" src="{image_path}" alt="Document Background">
            <div id="bboxes"></div>
            <div id="tooltip" class="tooltip"></div>
        </div>
    
        <script>
            const boundingBoxes = {json.dumps([{
                "x": block["bounding_box"][0][0],
                "y": block["bounding_box"][0][1],
                "width": block["bounding_box"][1][0] - block["bounding_box"][0][0],
                "height": block["bounding_box"][2][1] - block["bounding_box"][0][1],
                "text": block["text"]
            } for block in structured_data.get("blocks", [])], indent=4)};
    
            function displayBoundingBoxes() {{
                const container = document.getElementById("bboxes");
                const tooltip = document.getElementById("tooltip");
    
                boundingBoxes.forEach(box => {{
                    const div = document.createElement("div");
                    div.classList.add("bbox");
                    div.style.left = box.x + "px";
                    div.style.top = box.y + "px";
                    div.style.width = box.width + "px";
                    div.style.height = box.height + "px";
    
                    div.addEventListener("mouseover", (event) => {{
                        tooltip.style.display = "block";
                        tooltip.innerText = box.text;
                        tooltip.style.left = event.pageX + 10 + "px";
                        tooltip.style.top = event.pageY + 10 + "px";
                    }});
    
                    div.addEventListener("mouseout", () => {{
                        tooltip.style.display = "none";
                    }});
    
                    container.appendChild(div);
                }});
            }}
    
            displayBoundingBoxes();
        </script>
    
    </body>
    </html>
    """
    
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_template)
    
    print(f"✅ HTML file generated: {output_html}")
