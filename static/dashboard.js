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

document.getElementById("addClass").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent default form submission

    const className = document.getElementById("class").value;
    const grade = document.getElementById("grade").value;
    const credits = document.getElementById("credits").value;
    const year = document.getElementById("year").value;
    const type = document.getElementById("type").value;

    // Find the appropriate table based on the year
    const gradeTablesIndex = parseInt(year) - 9;
    const currentTable = gradeTables[gradeTablesIndex];

    const newRow = currentTable.insertRow();
    const cell1 = newRow.insertCell(0);
    const cell2 = newRow.insertCell(1);
    const cell3 = newRow.insertCell(2);
    
    if (type != "normal") {
        cell1.innerHTML = type + " " + className;
    }
    else {
        cell1.innerHTML = className;
    }

    cell2.innerHTML = grade;
    cell3.innerHTML = credits;

    document.getElementById("class").value = "";
    document.getElementById("grade").value = "";
    document.getElementById("credits").value = "";
    document.getElementById("year").value = "";
    document.getElementById("type").value = "";

    toggleVisibility();
});