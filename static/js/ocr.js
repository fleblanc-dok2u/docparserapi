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
  theme: 'snow'
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
  const offsetX = (image.clientWidth - scaleX * pageImage.width) / 2;

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
