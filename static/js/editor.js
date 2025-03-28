// Wait until all scripts are loaded
let editor;
window.addEventListener('DOMContentLoaded', () => {
    initEditor();
});

function initEditor(data = null) {
    editor = new EditorJS({
        holder: 'editorjs',
        autofocus: true,
        tools: {
            paragraph: {
                class: window.Paragraph,
                inlineToolbar: true,
            },
            header: {
                class: window.Header,
                inlineToolbar: true,
                config: {
                    levels: [3, 4, 5],
                    defaultLevel: 4,
                    "align": "left"
                },
                toolbox: {
                    title: 'Header',
                    icon: '🅷'
                },

            },
            list: {
                class: EditorjsList,
                inlineToolbar: true,
                config: {
                  defaultStyle: 'unordered'
                },
            },
            table: {
                class: window.Table,
                toolbox: {
                title: 'Table',
                icon: '📊'
                }
            },
            checklist: {
                class: window.Checklist,
                inlineToolbar: true,
                toolbox: {
                title: 'Checklist',
                icon: '✅'
                }
            },
            warning: {
                class: window.Warning,
                inlineToolbar: true,
                toolbox: {
                title: 'Warning',
                icon: '⚠️'
                }
            },
            delimiter: {
                class: window.Delimiter,
                toolbox: {
                title: 'Delimiter',
                icon: '➖'
                }
            },
            linkTool: {
                class: window.LinkTool,
                config: {
                    endpoint: 'https://your-api.com/fetchUrl' // Replace this with your backend endpoint
                },
                toolbox: {
                    title: 'Link',
                    icon: '🔗'
                }
            },
            image: {
                class: ImageTool,
                config: {
                  endpoints: {
                    byFile: '/uploadFile', // Your backend file uploader endpoint
                    byUrl: '/fetchUrl', // Your endpoint that provides uploading by Url
                  }
                }
                
            },
            callFunction: CropTool
        },
        data: data || {
            blocks: [
            {
                type: "header",
                data: {
                text: "Welcome to Editor.js",
                level: 2
                }
            },
            {
                type: "paragraph",
                data: {
                text: "You can edit this text, use formatting tools, and reset/save your content."
                }
            }
            ]
        },
        onReady: () => {
            new Undo({ editor }); //Enable undo
            new DragDrop(editor); // Enable drag-n-drop

        }
    });
  }


function saveDocument(){
    editor.save().then((outputData) => {
      console.log("Saved data: ", outputData);
      alert("Content saved! Check the console.");
    }).catch((error) => {
      console.error("Saving failed: ", error);
    });
}
function clearDocument() {
    const confirmed = confirm("⚠️ Are you sure you want to clear the document? This will delete all content.");
  
    if (confirmed) {
        editor.destroy();
        initEditor(); // Reinitialize editor
    }
  }
  
function clearAllBlocks(callback) {
    editor.blocks.clear().then(() => {
        if (typeof callback === 'function') {
            callback();
        }
        // Remove the first empty block (usually index 0)
        // But only if it is still there and empty
        setTimeout(() => {
            editor.blocks.delete(0);
        }, 100); // Short delay to ensure inserts are processed

    });
  }
function addTextToEditor(text,type){
    editor.blocks.insert(type, { text: text });

}
function addImageToEditor(blob,index){
    const reader = new FileReader();

    reader.onload = () => {
      const base64data = reader.result;
        
      editor.blocks.insert("image", {
        file: {
          url: base64data
        },
        withBorder: true,
        withBackground: false,
        stretched: false
      },index);
    }
    reader.readAsDataURL(blob);

}
function showWarningMessage(message,style){
    editor.notifier.show({
        message: message,
        style: style
      });

}