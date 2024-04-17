const emptyTexts = document.querySelectorAll(".emptyText");
const gradeTables = document.querySelectorAll(".grades");

emptyTexts.forEach(function(emptyText) {
    emptyText.style.display = "none";
});

function toggleVisibility() {
    emptyTexts.forEach(function(emptyText, index) {
        const table = gradeTables[index];
        const rowCount = table.querySelectorAll("tr").length;
        
        if (rowCount > 1) {
            emptyText.style.display = "none";
            table.style.display = "table";
        } else {
            emptyText.style.display = "block";
            table.style.display = "none";
        }
    });
}


toggleVisibility();
