// ================================
// Loader
// ================================

const form = document.querySelector("form");
const loader = document.getElementById("loader");

if (form && loader) {

    form.addEventListener("submit", function(e){

        e.preventDefault();

        loader.style.display = "flex";

        setTimeout(function(){

            form.submit();

        }, 150);

    });

}

// ================================
// Unlock PDF
// ================================

const pdfInput = document.getElementById("pdf");
const fileName = document.getElementById("file-name");

if(pdfInput && fileName){

    pdfInput.addEventListener("change", function(){

        if(this.files.length > 0){

            fileName.innerHTML = this.files[0].name;

        }else{

            fileName.innerHTML = "No file selected";

        }

    });

}

// ================================
// Merge PDF
// ================================

const pdfsInput = document.getElementById("pdfs");

if(pdfsInput && fileName){

    pdfsInput.addEventListener("change", function(){

        if(this.files.length === 0){

            fileName.innerHTML = "No file selected";

        }

        else if(this.files.length === 1){

            fileName.innerHTML = this.files[0].name;

        }

        else{

            fileName.innerHTML = this.files.length + " PDF files selected";

        }

    });

}