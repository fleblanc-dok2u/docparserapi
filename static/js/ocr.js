    let ocrData = null;
    let currentPage = 0;
    let pageImage= null;
    let pageBlocks= null;
    let usercode = Math.floor(100000 + Math.random() * 900000).toString();

    alert("Dev")
    window.addEventListener('resize', () => {
        console.log('resize')
        if (ocrData && pageBlocks && pageImage) {
            document.getElementById('bboxes').innerHTML = '';
            renderBBoxes(pageBlocks,pageImage);
        }
      });
      
    tinymce.init({
      selector: '#editor',
      height: '90vh',
      menubar: false,
      plugins: 'lists link charmap preview anchor code fullscreen',
      toolbar: 'undo redo | formatselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist | code'
    });

    function sendOCRFile(file) {


        ocrData = null;
        currentPage = 0;    
        // Show spinner
        document.getElementById("global-spinner").classList.remove("d-none");
        //Get file
        const formData = new FormData();
        formData.append("file", file);

        // Send user digit code
        formData.append("code", usercode);

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
            // Hide spinner
            document.getElementById("global-spinner").classList.add("d-none");
        });
    }
    function clearOCR() {
        document.getElementById('docImage').src = '';
        document.getElementById('bboxes').innerHTML = '';
        document.getElementById('ocrList').innerHTML = '';
        document.getElementById('ocr-warning').classList.add('d-none');
        document.getElementById('docImage').classList.add('d-none'); // hide it before loading

      }
      
    function renderPage() {
        //Clear layout
        clearOCR()
        //Return if no data
        if (!ocrData || !ocrData.images || currentPage >= ocrData.images.length) {
            showWarningMessage("No data available.");
            return;
        }

        pageImage = ocrData.images[currentPage];
        pageBlocks = ocrData.blocks.filter(block => block.page === pageImage.page);
      
        const img = document.getElementById('docImage');
        img.onload = () => {
            img.classList.remove('d-none'); // show after loaded
            // Now the image has loaded, and dimensions are available
            renderSections(pageBlocks);
            renderBBoxes(pageBlocks, pageImage);
        };
        img.onerror = () => {
            img.classList.add('d-none'); // keep it hidden if loading fails
        };
        img.src = pageImage.path;


      }
      

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
            div.id = `ocr-block-${i}`; // ID for linking

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
      
    function toggleAllCheckboxes(masterCheckbox) {
        const checkboxes = document.querySelectorAll('#ocrList input.form-check-input:not(#selectAllCheckbox)');
        checkboxes.forEach(cb => cb.checked = masterCheckbox.checked);
    }
      
    function renderBBoxes(blocks, pageImage) {
        const image = document.getElementById("docImage");
        const bboxesContainer = document.getElementById("bboxes");
        
        const scaleX = image.clientWidth / pageImage.width;
        const scaleY = scaleX;
      
        const offsetY = image.offsetTop;  // image margin-top inside container
        const offsetX = (image.clientWidth - scaleX * pageImage.width)/2; // image margin-left inside container

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

            // Highlight corresponding right-side block on hover
            div.setAttribute('onmouseenter', `highlightBBox(${i})`);
            div.setAttribute('onmouseleave', `unhighlightBBox(${i})`);  

            bboxesContainer.appendChild(div);
        });
    }

    function highlightBBox(index) {
        const box = document.getElementById(`bbox-${index}`);
        if (box) box.classList.add('highlight');
        const block = document.getElementById(`ocr-block-${index}`);
        if (block) block.classList.add('highlight');
    }
      
    function unhighlightBBox(index) {
        const box = document.getElementById(`bbox-${index}`);
        if (box) box.classList.remove('highlight');
        const block = document.getElementById(`ocr-block-${index}`);
        if (block) block.classList.remove('highlight');
    }
      
    function copySelected() {
      const checkboxes = document.querySelectorAll('#ocrList input:checked');
      if(checkboxes.length==0){
        showWarningMessage("No section selected.");
        return
      }
      const selected = Array.from(checkboxes).map(cb => cb.nextElementSibling.textContent.trim()).join("\n");
      navigator.clipboard.writeText(selected);
      showWarningMessage("Text copied to clipboard.");
    }

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


    function showWarningMessage(message) {
        const footer = document.getElementById("ocr-warning");
        footer.textContent = message;
        footer.classList.remove("d-none");
    }
