// === OCR Viewer Logic ===

// OCR data structure and state
let ocrData = null;
let currentPage = 0;
let pageImage = null;
let pageBlocks = null;

// Unique session ID for OCR uploads
let sessionid = Math.floor(100000 + Math.random() * 900000).toString();

// Re-render bounding boxes on window resize
window.addEventListener('resize', () => {
  if (ocrData && pageBlocks && pageImage) {
    document.getElementById('bboxes').innerHTML = '';
    renderBBoxes(pageBlocks, pageImage);
  }
});

// Initialize Quill editor
const quill = new Quill('#editor', {
    modules: {
        syntax: true,
        toolbar: '#toolbar-container',
      },
      placeholder: 'Write text...',
      theme: 'snow',
});


// Send file to backend for OCR
function sendOCRFile(file) {
  ocrData = null;
  currentPage = 0;
  document.getElementById("global-spinner").classList.remove("d-none");

  const formData = new FormData();
  formData.append("file", file);
  formData.append("sessionid", sessionid);

  fetch('/get_ocr', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      ocrData = data;
      currentPage = 0;
      renderPage();
    })
    .finally(() => {
      document.getElementById("global-spinner").classList.add("d-none");
    });
}

// Clear current OCR layout and image
function clearOCR() {
  document.getElementById('docImage').src = '';
  document.getElementById('bboxes').innerHTML = '';
  document.getElementById('ocrList').innerHTML = '';
  document.getElementById('ocr-warning').classList.add('d-none');
  document.getElementById('docImage').classList.add('d-none');
}

// Load image and render bounding boxes and sections
function renderPage() {
  clearOCR();
  if (!ocrData || !ocrData.images || currentPage >= ocrData.images.length) {
    showWarningMessage("No data available.");
    return;
  }

  pageImage = ocrData.images[currentPage];
  pageBlocks = ocrData.blocks.filter(block => block.page === pageImage.page);

  const img = document.getElementById('docImage');
  img.onload = () => {
    img.classList.remove('d-none');
    renderSections(pageBlocks);
    renderBBoxes(pageBlocks, pageImage);
    //drawTextBlocksAsTextAreas(pageBlocks, pageImage); // 👈 Add this line
  };

  img.onerror = () => {
    img.classList.add('d-none');
  };
  img.src = pageImage.path;
}

// Render the text sections on the right-hand panel
function renderSections(blocks) {
  const container = document.getElementById('ocrList');
  container.innerHTML = '';

  // Add Select All checkbox
  const selectAll = document.createElement('div');
  selectAll.className = 'form-check mb-2';
  selectAll.innerHTML = `
    <input class="form-check-input" type="checkbox" id="selectAllCheckbox" onchange="toggleAllCheckboxes(this)">
    <label class="form-check-label fw-bold" for="selectAllCheckbox">Select All</label>
  `;
  container.appendChild(selectAll);

  blocks.forEach((block, i) => {
    const div = document.createElement('div');
    div.className = 'ocr-block';
    div.id = `ocr-block-${i}`;
    div.innerHTML = `
      <div class="form-check">
        <input class="form-check-input" type="checkbox" id="check${i}" data-index="${i}">
        <label class="form-check-label" for="check${i}">${block.text}</label>
      </div>
    `;
    div.setAttribute('onmouseenter', `highlightBBox(${i})`);
    div.setAttribute('onmouseleave', `unhighlightBBox(${i})`);
    div.addEventListener('click', () => showToolAtBBox(i));
    container.appendChild(div);
  });
}

// Toggle checkboxes based on the master checkbox
function toggleAllCheckboxes(masterCheckbox) {
  const checkboxes = document.querySelectorAll('#ocrList input.form-check-input:not(#selectAllCheckbox)');
  checkboxes.forEach(cb => cb.checked = masterCheckbox.checked);
}

// Render bounding boxes on the image
function renderBBoxes(blocks, pageImage) {
  const image = document.getElementById("docImage");
  const bboxesContainer = document.getElementById("bboxes");
  const scaleX = image.clientWidth / pageImage.width;
  const scaleY = scaleX;
  const offsetY = image.offsetTop;
  const offsetX = image.offsetLeft; //(image.clientWidth - scaleX * pageImage.width) / 2;

  bboxesContainer.innerHTML = '';
  blocks.forEach((block, i) => {
    const div = document.createElement("div");
    div.className = "bbox";
    div.id = `bbox-${i}`;

    const x = block.bounding_box[0][0] * scaleX + offsetX;
    const y = block.bounding_box[0][1] * scaleY + offsetY;
    const width = (block.bounding_box[1][0] - block.bounding_box[0][0]) * scaleX;
    const height = (block.bounding_box[2][1] - block.bounding_box[0][1]) * scaleY;

    div.style.left = `${x}px`;
    div.style.top = `${y}px`;
    div.style.width = `${width}px`;
    div.style.height = `${height}px`;

    div.setAttribute('onmouseenter', `highlightBBox(${i})`);
    div.setAttribute('onmouseleave', `unhighlightBBox(${i})`);
    bboxesContainer.appendChild(div);
  });
}

// Highlight matching bbox and section
function highlightBBox(index) {
  document.getElementById(`bbox-${index}`)?.classList.add('highlight');
  document.getElementById(`ocr-block-${index}`)?.classList.add('highlight');
}

function unhighlightBBox(index) {
  document.getElementById(`bbox-${index}`)?.classList.remove('highlight');
  document.getElementById(`ocr-block-${index}`)?.classList.remove('highlight');
}

// Copy selected text blocks to clipboard
function copySelected() {
  const checkboxes = document.querySelectorAll('#ocrList input:checked');
  if (checkboxes.length === 0) {
    showWarningMessage("No section selected.");
    return;
  }
  const selected = Array.from(checkboxes).map(cb => cb.nextElementSibling.textContent.trim()).join("\n");
  navigator.clipboard.writeText(selected);
  showWarningMessage("Text copied to clipboard.");
}

// Image area selection to copy image clip
let isSelecting = false;
let startX, startY, endX, endY;
let paddingTop, paddingLeft;
const selectionBox = document.getElementById('selection-box');
const image = document.getElementById("docImage");

function enableAreaSelection() {
  document.getElementById('bboxes').style.display = 'none';
  const ocrLeft = document.querySelector('.ocr-left');
  const style = window.getComputedStyle(ocrLeft);
  paddingTop = parseFloat(style.paddingTop);
  paddingLeft = parseFloat(style.paddingLeft);

  image.style.cursor = 'crosshair';
  document.addEventListener('mousedown', startSelection);
  document.addEventListener('mousemove', updateSelection);
  document.addEventListener('mouseup', finishSelection);
}

function startSelection(e) {
  isSelecting = true;
  const rect = image.getBoundingClientRect();
  startX = e.clientX - rect.left + paddingLeft;
  startY = e.clientY - rect.top + paddingTop;

  selectionBox.style.left = `${startX}px`;
  selectionBox.style.top = `${startY}px`;
  selectionBox.style.width = '0px';
  selectionBox.style.height = '0px';
  selectionBox.style.display = 'block';
}

function updateSelection(e) {
  try {
    if (!isSelecting) return;
    const rect = image.getBoundingClientRect();
    endX = Math.max(paddingLeft, Math.min(rect.width + paddingLeft, e.clientX - rect.left + paddingLeft));
    endY = Math.max(paddingTop, Math.min(rect.height + paddingTop, e.clientY - rect.top + paddingTop));

    const x = Math.min(startX, endX);
    const y = Math.min(startY, endY);
    const w = Math.abs(endX - startX);
    const h = Math.abs(endY - startY);

    selectionBox.style.left = `${x}px`;
    selectionBox.style.top = `${y}px`;
    selectionBox.style.width = `${w}px`;
    selectionBox.style.height = `${h}px`;
  } catch (err) {
    console.error('updateSelection failed:', err);
  }
}

function finishSelection(e) {
  if (!isSelecting) return;
  isSelecting = false;
  image.style.cursor = 'default';
  document.removeEventListener('mousedown', startSelection);
  document.removeEventListener('mousemove', updateSelection);
  document.removeEventListener('mouseup', finishSelection);
  document.getElementById('bboxes').style.display = 'block';

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const scaleX = image.naturalWidth / image.clientWidth;
  const scaleY = image.naturalHeight / image.clientHeight;

  const sx = Math.min(startX, endX) * scaleX;
  const sy = Math.min(startY, endY) * scaleY;
  const sw = Math.abs(endX - startX) * scaleX;
  const sh = Math.abs(endY - startY) * scaleY;

  canvas.width = sw;
  canvas.height = sh;

  const img = new Image();
  img.src = image.src;
  img.onload = () => {
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
    canvas.toBlob(blob => {
      navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
      selectionBox.style.display = 'none';
    });
  };
  showWarningMessage("Image copied to clipboard.");
}

// Navigate pages
function pageUp() {
  if (!ocrData || !ocrData.images) return;
  if (currentPage > 0) {
    currentPage--;
    renderPage();
  } else {
    showWarningMessage("You're already on the first page.");
  }
}

function pageDown() {
  if (!ocrData || !ocrData.images) return;
  if (currentPage < ocrData.images.length - 1) {
    currentPage++;
    renderPage();
  } else {
    showWarningMessage("You're already on the last page.");
  }
}

// Show warnings to the user
function showWarningMessage(message) {
  const warning = document.getElementById("ocr-warning");
  warning.textContent = message;
  warning.classList.remove("d-none");
  setTimeout(() => warning.classList.add("d-none"), 5000);
}

function drawTextBlocksAsTextAreas(blocks, pageImage) {
  const image = document.getElementById("docImage");
  const container = document.querySelector(".ocr-right");

  // Clear previous textareas
  document.querySelectorAll('.ocr-textarea').forEach(el => el.remove());

  const scaleX = image.clientWidth / pageImage.width;
  const scaleY = scaleX;
  const paddingX=5
  const paddingY=5
  // Create temporary canvas for text measurement
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  blocks.forEach((block, i) => {
    if (!block.text || block.text.trim() === "") return;

    const bbox = block.bounding_box;

    // Handle line breaks
    const lines = block.text.split('\n').filter(line => line.trim().length > 0);


    const x = bbox[0][0] * scaleX;
    const y = bbox[0][1] * scaleY;
    const width =  (bbox[1][0] - bbox[0][0]) * scaleX;
    const height =  (bbox[2][1] - bbox[0][1]) * scaleY;

    // Fit text inside bounding box
    const fontSize = getFittingFontSize(ctx, lines, width, height);
    const textarea = document.createElement("textarea");
    textarea.className = "ocr-textarea";
    textarea.value = block.text.replace(/\n+$/, '');;
    textarea.style.position = "absolute";
    textarea.style.left = `${x}px`;
    textarea.style.top = `${y}px`;

    textarea.style.width = `${width}px`;
    textarea.style.height = `${height}px`;
    textarea.style.border = "1px solid #666";
    textarea.style.padding = `0px`;
    textarea.style.backgroundColor = "rgba(255,255,255,0.8)";
    textarea.style.fontSize = `${fontSize}px`;
    textarea.style.fontFamily = "Arial";

    container.appendChild(textarea);
    autoResizeTextarea(textarea,height+fontSize);
    makeTextareaDraggable(textarea, {
      gridSize: 5,
      container: document.querySelector('.ocr-right')
    });

    // const div = document.createElement("div");
    // div.className = "editor-block editable-block";
    // div.dataset.index = i;
    // div.style.position = "absolute";
    // div.style.left = `${x}px`;
    // div.style.top = `${y}px`;
    // div.style.width = `${width}px`;
    // div.style.minHeight = `${height}px`;
    // div.style.overflow = "hidden";
    // div.style.background = "rgba(255,255,255,0.8)";
    // div.style.border = "1px solid #666";
    // div.style.padding = "4px";
    // div.style.cursor = "pointer";
    // div.style.fontSize = `${fontSize}px`;
    // div.style.fontFamily = "Arial";
    // div.innerHTML = block.text.replace(/\n+$/, '').replace(/\n/g, "<br>");
    // div.addEventListener("click", () => activateEditorOnDiv(div, block));
    // container.appendChild(div);
    

  });
}

// 🔧 Adjust font size to fit text into bbox
function getFittingFontSize(ctx, lines, maxWidth, maxHeight) {
  // ✅ Remove empty or whitespace-only lines
  const lineCount = lines.length;

  let fontSize = 20;

  while (fontSize > 4) {
    ctx.font = `${fontSize}px Arial`;

    const fitsHorizontally = lines.every(line => ctx.measureText(line).width <= maxWidth);
    const fitsVertically = fontSize * lineCount <= maxHeight;

    if (fitsHorizontally && fitsVertically) {
      break;
    }

    fontSize -= 1;
  }

  return fontSize;
}
function autoResizeTextarea(textarea, maxHeight = 1000) {
  let newHeight = textarea.scrollHeight;

  // Optional: incrementally grow (more visually gradual)
  while (textarea.scrollHeight > textarea.clientHeight && newHeight < maxHeight) {
    newHeight += 2;
    textarea.style.height = `${newHeight}px`;
  }

  // Set final height
  textarea.style.height = `${newHeight+2}px`;
}

function makeTextareaDraggable(textarea, options = {}) {
  const {
    gridSize = 10,
    container = document.querySelector('.ocr-right'),
  } = options;

  let offsetX = 0, offsetY = 0;
  let isDragging = false;

  textarea.style.cursor = 'move';
  textarea.style.position = 'absolute';
  console.log('Container:', container.getBoundingClientRect());
  console.log('Textarea offset:', textarea.offsetLeft, textarea.offsetTop);

  textarea.addEventListener('mousedown', (e) => {
    isDragging = true;
    const containerRect = container.getBoundingClientRect();
    offsetX = e.clientX - containerRect.left - textarea.offsetLeft;
    offsetY = e.clientY - containerRect.top - textarea.offsetTop;
    console.log('e.client:',  e.clientX, e.clientY);
    console.log('offset:', offsetX, offsetY);

    textarea.style.zIndex = 1000;
    e.preventDefault();
  });

  document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    // Calculate new position
    const containerRect = container.getBoundingClientRect();
    const newX = Math.max(0, Math.min(container.clientWidth - textarea.offsetWidth, e.clientX - containerRect.left - offsetX));
    const newY = Math.max(0, Math.min(container.clientHeight - textarea.offsetHeight, e.clientY - containerRect.top - offsetY));

    // Snap to grid
    const snappedX = Math.round(newX / gridSize) * gridSize;
    const snappedY = Math.round(newY / gridSize) * gridSize;

    textarea.style.left = `${snappedX}px`;
    textarea.style.top = `${snappedY}px`;
  });

  document.addEventListener('mouseup', () => {
    if (isDragging) {
      isDragging = false;
    }
  });
}


let activeEditor = null;

function activateEditorOnDiv(div, block) {
  if (activeEditor) return; // Prevent multiple editors

  const container = document.createElement("div");
  const holderId = `editor-${Date.now()}`;
  container.id = holderId;
  container.className = "editor-block";
  container.style.position = "absolute";
  container.style.left = div.style.left;
  container.style.top = div.style.top;
  container.style.width = div.style.width;
  container.style.minHeight = div.style.minHeight;
  container.style.padding = div.style.padding;
  container.style.border = div.style.border;
  container.style.background = div.style.background;

  div.replaceWith(container);

  activeEditor = new EditorJS({
    holder: holderId,
    tools: {
      bold: window.Bold,
      italic: window.Italic,
      underline: window.Underline
    },
    inlineToolbar: ['bold', 'italic', 'underline'],
    data: {
      blocks: [{
        type: "text",
        data: { text: block.text.replace(/\n+$/, '').replace(/\n/g, "<br>") }
      }]
    },
    onReady: () => {
      const editorDOM = container.querySelector('[contenteditable]');
      editorDOM.focus();
    },
    onBlur: async () => {
      const saved = await activeEditor.save();
      const html = saved.blocks.map(b => b.data.text).join("<br>");
      block.text = saved.blocks.map(b => b.data.text).join("\n");

      const restoredDiv = document.createElement("div");
      restoredDiv.className = "editor-block editable-block";
      restoredDiv.style.cssText = container.style.cssText;
      restoredDiv.innerHTML = html;
      restoredDiv.addEventListener("click", () => activateEditorOnDiv(restoredDiv, block));

      container.replaceWith(restoredDiv);
      activeEditor = null;
    }
  });
}
