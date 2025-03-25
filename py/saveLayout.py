import os
import json
from PIL import Image
import html

def get_image_size(image_path):
    """ Returns the width and height of an image. """
    with Image.open(image_path) as img:
        return img.width, img.height

def generate_html_with_bboxes(structured_data, image_path, output_html="output.html", template_file="template.html"):
    """
    Generates an HTML page using a template and filling it with bounding box data.
    Highlights the bounding box when hovering over text on the left.
    Adds a copy button for each text section.
    
    Parameters:
    - structured_data (dict): Contains 'blocks' (text and bbox data).
    - image_path (str): Path to the background image.
    - output_html (str): Path to save the generated HTML file.
    - template_html (str): Path to the HTML template file.
    """

    orig_width, orig_height = get_image_size(image_path)


    # Generate the dynamic text blocks with <br> per line
    text_blocks = "".join(
        [
            f'<div class="ocr-box" data-index="{i}" onmouseover="highlightBBox({i})" onmouseout="removeHighlight({i})">'
            f'{"<br>".join(block["text"].splitlines())} '
            f'<button class="copy-btn" onclick="copyText({i})">📋</button></div>'
            for i, block in enumerate(structured_data.get("blocks", []))
        ]
    )
    
    # Prepare block data for JavaScript rendering
    bbox_data_json = json.dumps(structured_data.get("blocks", []))

    # Load template
    with open(template_file, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Replace placeholders
    html_content = html_template.replace("{{ TEXT_BLOCKS }}", text_blocks)
    html_content = html_content.replace("{{ IMAGE_PATH }}", os.path.basename(image_path))
    html_content = html_content.replace("{{ BBOX_DATA_JSON }}", bbox_data_json)
    html_content = html_content.replace("{{ ORIGINAL_WIDTH }}", str(orig_width))
    html_content = html_content.replace("{{ ORIGINAL_HEIGHT }}", str(orig_height))

    # Write the final HTML file
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTML file generated: {output_html} using template: {template_file}")
