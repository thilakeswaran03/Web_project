document.addEventListener("DOMContentLoaded", function () { 
    const regNoInput = document.getElementById("reg_no");
    const studentInfoDiv = document.getElementById("student-info");
    const creditSummaryDiv = document.getElementById("credit-summary");
    const completedCoursesDiv = document.getElementById("completed-courses");

    // Hide elements initially
    studentInfoDiv.style.display = "none";
    creditSummaryDiv.style.display = "none";
    completedCoursesDiv.style.display = "none";

    // Trigger search on Enter key
    regNoInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            fetchCreditDetails();
        }
    });
});

// Mapping of abbreviations to full category names for display
const CATEGORY_ABBREVIATIONS = {
    "BS": "Basic Science",
    "EEC": "Employability Enhancement Courses",
    "ES": "Engineering Sciences",
    "MC": "Mandatory Courses",
    "PC": "Professional Core",
    "PE": "Professional Elective",
    "OE": "Open Elective",
    "HS": "Humanities & Social Science",
    "TOTAL": "Total Credits"
};

function fetchCreditDetails() {
    let reg_no = document.getElementById("reg_no").value.trim();
    let studentInfoDiv = document.getElementById("student-info");
    let creditSummaryDiv = document.getElementById("credit-summary");
    let completedCoursesDiv = document.getElementById("completed-courses");

    // Hide previous results
    studentInfoDiv.style.display = "none";
    creditSummaryDiv.style.display = "none";
    completedCoursesDiv.style.display = "none";
    completedCoursesDiv.innerHTML = ""; // Clear previous course details

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
            throw new Error(data.error);
        }
        displayStudentInfo(data.student_info);
        displayCreditDetails(data.student_credit_info, data.total_credit_info);
    })
    .catch(error => {
        studentInfoDiv.innerHTML = `<p style="color: red;">${error.message}</p>`;
        studentInfoDiv.style.display = "block";
        console.error("Error:", error);
    });
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

    console.log("Received Earned Credits:", earnedCredits);
    console.log("Received Total Credits:", totalCredits);

    let tableRows = Object.keys(totalCredits || {}).map(categoryAbbr => {
        if (categoryAbbr === "TOTAL") return ""; // Skip total row

        let totalCredit = totalCredits[categoryAbbr] || 0;
        let earnedCredit = earnedCredits[categoryAbbr] || 0;
        let remainingCredit = Math.max(totalCredit - earnedCredit, 0); // Ensure no negative values

        // Get full category name for display
        let categoryName = CATEGORY_ABBREVIATIONS[categoryAbbr] || categoryAbbr;

        return `
            <tr class="category-row" data-category="${categoryAbbr}" style="cursor: pointer;">
                <td>${categoryName}</td>
                <td>${totalCredit}</td>
                <td>${earnedCredit}</td>
                <td style="color: ${remainingCredit > 0 ? 'red' : 'green'};">${remainingCredit}</td>
            </tr>
        `;
    }).join("");

    let totalRequired = totalCredits["TOTAL"] || 0;
    let totalEarned = Object.keys(earnedCredits || {})
        .filter(category => category !== "TOTAL")
        .reduce((sum, key) => sum + earnedCredits[key], 0);
    let totalRemaining = Math.max(totalRequired - totalEarned, 0);

    creditSummaryDiv.innerHTML = `
        <h3>Credit Summary</h3>
        <table border="1">
            <tr>
                <th>Category</th>
                <th>Total Required Credits</th>
                <th>Earned Credits</th>
                <th>Remaining Credits</th>
            </tr>
            ${tableRows}
            <tr style="font-weight: bold; background:rgba(86, 71, 71, 0.5);">
                <td>Total</td>
                <td>${totalRequired}</td>
                <td>${totalEarned}</td>
                <td style="color: ${totalRemaining > 0 ? 'red' : 'green'};">${totalRemaining}</td>
            </tr>
        </table>
    `;
    creditSummaryDiv.style.display = "block";

    // Attach click event listener to rows
    document.querySelectorAll(".category-row").forEach(row => {
        row.addEventListener("click", function () {
            let categoryAbbr = this.getAttribute("data-category");
            let reg_no = document.getElementById("reg_no").value.trim();

            fetchCompletedCourses(reg_no, categoryAbbr);
        });
    });
}

function fetchCompletedCourses(reg_no, categoryAbbr) {
    if (!reg_no || !categoryAbbr) {
        alert("Invalid register number or category.");
        return;
    }

    fetch("/get_completed_courses", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ reg_no: reg_no, category: categoryAbbr }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showCompletedCourses(data.category, data.courses);
    })
    .catch(error => {
        console.error("Error fetching completed courses:", error);
        alert(`Error fetching completed courses for ${categoryAbbr}.`);
    });
}

function showCompletedCourses(categoryAbbr, courses) {
    try {
        console.log(`Category: ${categoryAbbr}`);
        console.log(`Extracted courses:`, courses);

        let completedCoursesDiv = document.getElementById("completed-courses");

        if (!Array.isArray(courses) || courses.length === 0) {
            completedCoursesDiv.innerHTML = `<p style="color: red;">No completed courses found for ${CATEGORY_ABBREVIATIONS[categoryAbbr] || categoryAbbr}.</p>`;
            completedCoursesDiv.style.display = "block";
            return;
        }

        let coursesTable = `
            <h4>${CATEGORY_ABBREVIATIONS[categoryAbbr] || categoryAbbr} - Completed Courses</h4>
            <table border="1">
                <tr>
                    <th>Course Code</th>
                    <th>Course Title</th>
                    <th>Theory Credits</th>
                    <th>Practical Credits</th>
                    <th>Total Credits</th>
                </tr>
                ${courses.map(course => `
                    <tr>
                        <td>${course["Course Code"] || "N/A"}</td>
                        <td>${course["Course Title"] || "N/A"}</td>
                        <td>${course["Theory Credits"] || "N/A"}</td>
                        <td>${course["Practical Credits"] || "N/A"}</td>
                        <td>${course["Total Credits"] || "N/A"}</td>                  
                    </tr>
                `).join("")}
            </table>
        `;

        completedCoursesDiv.innerHTML = coursesTable;
        completedCoursesDiv.style.display = "block";
    } catch (error) {
        console.error("Error displaying completed courses:", error);
        alert("Error displaying completed courses.");
    }
}
