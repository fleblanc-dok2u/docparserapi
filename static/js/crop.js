class CropTool {
    static get toolbox() {
      return {
        title: 'Crop',
        icon: '✂️'
      };
    }
  
    constructor({ data, api }) {
      this.api = api;
      this.data = data || {};
      this.images = this.data.images || [];
      this.currentIndex = this.data.currentIndex || 0;
      this.croppedImages = this.data.croppedImages || [];
      this.cropper = null;
      this.imageElement = null;
      this.wrapper = null;
    }
  
    render() {

      if(ocrData==null || ocrData.images.length==0){
        showWarningMessage('Please load document first.','error')
        const wrapper = document.createElement('div');
        wrapper.className = 'my-block-wrapper';
        wrapper.innerText = '⚠️ No image provided. Please load one first.';
        wrapper.style.color = 'red';
        return wrapper;
      }
      this.wrapper = document.createElement('div');
      this.wrapper.className = 'crop-tool-wrapper';
 
      // Navigation
      const nav = document.createElement('div');
      nav.className = 'mt-3 d-flex justify-content-center gap-3';
      nav.style.padding = '5px'; 

      const prevBtn = document.createElement('button');
      prevBtn.innerText = '⬆️ Prev';
      prevBtn.className = 'btn btn-secondary';
      prevBtn.onclick = () => this.showImage(this.currentIndex - 1);
  
      const nextBtn = document.createElement('button');
      nextBtn.innerText = '⬇️ Next';
      nextBtn.className = 'btn btn-secondary';
      nextBtn.onclick = () => this.showImage(this.currentIndex + 1);

      const cropBtn = document.createElement('button');
      cropBtn.innerText = '✅ Save';
      cropBtn.className = 'btn btn-success';
      cropBtn.onclick = () => this.cropCurrentImage();

      // ❌ Cancel button
      const cancelBtn = document.createElement('button');
      cancelBtn.innerText = '❌ Cancel';
      cancelBtn.className = 'btn btn-outline-secondary';
      cancelBtn.onclick = () => {
        const index = this.api.blocks.getCurrentBlockIndex();
        if (index !== -1) {
          this.api.blocks.delete(index);
        }
      };

      nav.appendChild(prevBtn);
      nav.appendChild(nextBtn);
      nav.appendChild(cropBtn);
      nav.appendChild(cancelBtn);

      this.wrapper.appendChild(nav);

       // Image display
       this.imageElement = document.createElement('img');
       this.imageElement.style.maxWidth = '100%';
       this.imageElement.style.display = 'block';
       this.imageElement.style.margin = 'auto';
       this.wrapper.appendChild(this.imageElement); 
  
      // Load first image
      //this.showImage(this.currentIndex);
      const pathsOnly = ocrData.images.map(img => img.path);
      this.updateImageList(pathsOnly)
  
      return this.wrapper;
    }
  
    showImage(index) {
      if (index < 0 || index >= this.images.length) {
        showWarningMessage('No more images.','info')
        return;
      }
  
      this.currentIndex = index;
      if (this.cropper) this.cropper.destroy();
  
      const imageUrl = this.images[this.currentIndex];
      this.imageElement.src = imageUrl;
  
      this.imageElement.onload = () => {
        const { naturalWidth, naturalHeight } = this.imageElement;
        const maxWidth = 500;
        const ratio = naturalWidth / naturalHeight;
        const displayHeight = maxWidth / ratio;
  
        this.imageElement.style.width = `${maxWidth}px`;
        this.imageElement.style.height = `${displayHeight}px`;
  
        this.cropper = new Cropper(this.imageElement, {
          viewMode: 1,
          autoCropArea: 0.8,
          responsive: true
        });
      };
    }
  
    cropCurrentImage() {
      if (!this.cropper) return;
  
      const canvas = this.cropper.getCroppedCanvas({ width: 400, height: 200 });
  
      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'cropped.png', { type: 'image/png' });
  
        const formData = new FormData();
        formData.append('image', file);
  
        try {
          const response = await fetch('/uploadFile', {
            method: 'POST',
            body: formData
          });
  
          const result = await response.json();
  
          if (result.success && result.file?.url) {
            this.croppedImages.push({
              index: this.currentIndex,
              path: this.images[this.currentIndex].path || '',
              uploadedUrl: result.file.url
            });
            // Clean UI: remove cropper and show final image only
            this.wrapper.innerHTML = '';
            const finalImg = document.createElement('img');
            finalImg.src = result.file.url;
            finalImg.style.maxWidth = '100%';
            finalImg.style.display = 'block';
            finalImg.style.margin = 'auto';
            this.wrapper.appendChild(finalImg);
            showWarningMessage('✅ Image uploaded!','success')

          } else {
            throw new Error('Upload failed');
          }
        } catch (err) {
          showWarningMessage('❌ Upload error: ' + err.message,'error')

        }
      }, 'image/png');
    }
  
    updateImageList(newList) {
      this.images = newList;
      this.currentIndex = 0;
      this.showImage(0);
    }
  
    save() {
      return {
        images: this.images,
        currentIndex: this.currentIndex,
        croppedImages: this.croppedImages
      };
    }
  }
  
