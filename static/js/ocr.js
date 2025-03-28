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
      renderSections(ocrData.blocks);
    })
    .finally(() => {
      document.getElementById("global-spinner").classList.add("d-none");
    });
}


// Render the text sections on the right-hand panel
function renderSections(blocks) {
  //Clear all blocks
  clearAllBlocks(()=>{
    blocks.forEach((block, i) => {
      // Handle line breaks
      const lines = block.text.split('\n').filter(line => line.trim().length > 0);
     if(lines.length==1)
         addTextToEditor(block.text,'header')
     else
     if(lines.length>1)
         addTextToEditor(block.text,'paragraph')
   });

  })
 
}
 
