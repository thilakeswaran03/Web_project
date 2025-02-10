document.addEventListener("DOMContentLoaded", function () {
    const regNoInput = document.getElementById("reg_no");
    const studentInfoDiv = document.getElementById("student-info");
    const creditSummaryDiv = document.getElementById("credit-summary");

    // Hide student info and credit summary initially
    studentInfoDiv.style.display = "none";
    creditSummaryDiv.style.display = "none";

    // Trigger search on Enter key
    regNoInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            fetchCreditDetails();
        }
    });
});

function fetchCreditDetails() {
    let reg_no = document.getElementById("reg_no").value.trim();
    let studentInfoDiv = document.getElementById("student-info");
    let creditSummaryDiv = document.getElementById("credit-summary");

    // Hide previous results
    studentInfoDiv.style.display = "none";
    creditSummaryDiv.style.display = "none";

    if (reg_no === "") {
        alert("Please enter a Register Number.");
        return;
    }

    fetch("/credit_details", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ reg_no: reg_no }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            studentInfoDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
            creditSummaryDiv.innerHTML = "";
            studentInfoDiv.style.display = "block";
        } else {
            displayStudentInfo(data.student_info);
            displayCreditDetails(data.student_credit_info, data.total_credit_info);
        }
    })
    .catch(error => console.error("Error:", error));
}

function displayStudentInfo(info) {
    let studentInfoDiv = document.getElementById("student-info");
    studentInfoDiv.innerHTML = `
        <h3>Student Details</h3>
        <p><strong>Register No:</strong> ${info.reg_no || "N/A"}</p>
        <p><strong>Department:</strong> ${info.department || "N/A"}</p>
        <p><strong>Year:</strong> ${info.student_year || "N/A"}</p>
        <p><strong>Regulation:</strong> ${info.regulation || "N/A"}</p>
    `;
    studentInfoDiv.style.display = "block";
}

function displayCreditDetails(earnedCredits, totalCredits) {
    let creditSummaryDiv = document.getElementById("credit-summary");

    // Mapping short category names to full names
    let categoryFullNames = {
        "HS": "Humanities and Social Sciences",
        "BS": "Basic Sciences",
        "ES": "Engineering Sciences",
        "PC": "Professional Core",
        "PE": "Professional Electives",
        "OE": "Open Electives",
        "EEC": "Employability Enhancement Courses",
        "MC": "Mandatory Courses"
    };

    let tableRows = Object.keys(totalCredits || {}).map(categoryAbbr => {
        let totalCredit = totalCredits[categoryAbbr] || 0;
        let earnedCredit = earnedCredits[categoryAbbr] || 0;
        let remainingCredit = totalCredit - earnedCredit;
        let fullCategoryName = categoryFullNames[categoryAbbr] || categoryAbbr; // Default to the abbreviation if not found

        return `
            <tr>
                <td>${fullCategoryName}</td>
                <td>${totalCredit}</td>
                <td>${earnedCredit}</td>
                <td style="color: ${remainingCredit > 0 ? 'red' : 'green'};">${remainingCredit}</td>
            </tr>
        `;
    }).join("");

    creditSummaryDiv.innerHTML = `
        <h3>Credit Summary</h3>
        <p><strong>Name:</strong> ${earnedCredits.name || "N/A"}</p>
        <table border="1">
            <tr>
                <th>Category</th>
                <th>Total Required Credits</th>
                <th>Earned Credits</th>
                <th>Remaining Credits</th>
            </tr>
            ${tableRows}
        </table>
    `;
    creditSummaryDiv.style.display = "block";
}
