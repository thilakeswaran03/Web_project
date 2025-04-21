document.addEventListener("DOMContentLoaded", () => {
    // Element references
    const regNoInput = document.getElementById("registerNumber");
    const errorElement = document.getElementById("error");
    const detailsContainer = document.getElementById("detailsContainer");
    const courseNameInput = document.getElementById("courseName");
    const checkEligibilityButton = document.getElementById("checkEligibilityButton");
    const eligibilityResultElement = document.getElementById("eligibilityResult");
    const courseDetailsElement = document.getElementById("courseDetails");
    const suggestionsList = document.getElementById("suggestionsList");

    let typingTimer;
    const delay = 500; // Delay for debounce

    /**
     * Fetch student and course details
     */
    const fetchStudentDetails = async (regNo, courseName = null) => {
        try {
            const requestBody = courseName
                ? { reg_no: regNo, course_name: courseName }
                : { reg_no: regNo };

            const response = await fetch("/online_courses", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(requestBody),
            });
            const data = await response.json();
            
            if (!response.ok) throw new Error(data.error || "Unknown error");

            if (data.error) {
                showError(data.error);
                clearDisplay();
            } else {
                displayStudentDetails(data);
                if (courseName) displayCourseDetails(data);
            }
        } catch (error) {
            showError("An error occurred while checking eligibility. Please try again.");
            console.error("Fetch error:", error);
            clearDisplay();
        }
    };

    /**
     * Fetch autocomplete suggestions for course names
     */
    const fetchAutocompleteSuggestions = async (regNo, query) => {
        try {
            const response = await fetch(`/autocomplete?reg_no=${regNo}&query=${query}`);
            const data = await response.json();
    
            if (!response.ok) throw new Error("Failed to fetch autocomplete suggestions");
    
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions, query);
            } else {
                suggestionsList.innerHTML = "";
                suggestionsList.classList.add("hidden");
            }
        } catch (error) {
            console.error("Autocomplete fetch error:", error);
        }
    };    

    /**
     * Display student details
     */
    const displayStudentDetails = (data) => {
        errorElement.textContent = "";
        detailsContainer.classList.remove("hidden");
        
        // Update student details
        document.getElementById("studentRegNo").textContent = data.reg_no;
        document.getElementById("studentDepartment").textContent = data.department;
        document.getElementById("studentYear").textContent = data.student_year;
        document.getElementById("studentRegulation").textContent = data.regulation;
    };

    /**
     * Display course details
     */
    const displayCourseDetails = (data) => {
        eligibilityResultElement.classList.remove("hidden");
        //eligibilityResultElement.textContent = `Eligibility: ${data.eligibility}`;
        if (data.eligibility === "Not Eligible") {
            eligibilityResultElement.textContent = `${"This is your professional core. you are not suggested to enroll this course. (Credits will not be added in your account"})`;
        } else{
            eligibilityResultElement.textContent = `${"you can enroll this course"}`;
        }
        eligibilityResultElement.style.color = data.eligibility.includes("Not Eligible") ? "red" : "green";
    
        if (data.eligibility === "Eligible") {
            courseDetailsElement.classList.remove("hidden");
            document.getElementById("course_name").textContent = data.course_name;
            document.getElementById("platform").textContent = data.platform || "N/A";
            document.getElementById("course_code_R2019").textContent = data.course_code_R2019 || "N/A";
            document.getElementById("course_code_R2024").textContent = data.course_code_R2024 || "N/A";
            document.getElementById("credits").textContent = data.credits || "N/A";
            document.getElementById("duration").textContent = data.duration || "N/A";
            
            const linkElement = document.getElementById("link");
            linkElement.href = data.link || "#";
            linkElement.textContent = data.link ? "View Course" : "N/A";
        } else {
            courseDetailsElement.classList.add("hidden");
        }
    };    

    /**
     * Display autocomplete suggestions
     */
    const displaySuggestions = (courses, query) => {
        if (courses.length === 0) {
            suggestionsList.classList.add("hidden");
            return;
        }
    
        suggestionsList.innerHTML = courses.map((course) => `<li>${course}</li>`).join("");
        suggestionsList.classList.remove("hidden");
    };

    /**
     * Clear displayed data
     */
    const clearDisplay = () => {
        detailsContainer.classList.add("hidden");
        courseDetailsElement.classList.add("hidden");
        suggestionsList.classList.add("hidden");
        eligibilityResultElement.textContent = "";
        suggestionsList.innerHTML = "";
    };

    /**
     * Show error messages
     */
    const showError = (message) => {
        errorElement.textContent = message;
    };

    /**
     * Event Listeners
     */
    regNoInput.addEventListener("input", () => {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(() => {
            const regNo = regNoInput.value.trim();
            if (/^\d{12}$/.test(regNo)) {
                showError("");
                fetchStudentDetails(regNo);
            } else {
                showError("Enter a valid 12-digit register number.");
                clearDisplay();
            }
        }, delay);
    });

    courseNameInput.addEventListener("input", () => {
        const regNo = regNoInput.value.trim();
        const query = courseNameInput.value.trim();
        if (/^\d{12}$/.test(regNo) && query) fetchAutocompleteSuggestions(regNo, query);
    });

    suggestionsList.addEventListener("click", (event) => {
        if (event.target.tagName === "LI") {
            courseNameInput.value = event.target.textContent;
            suggestionsList.classList.add("hidden");
        }
    });

    document.addEventListener("click", (event) => {
        if (!suggestionsList.contains(event.target) && event.target !== courseNameInput) {
            suggestionsList.classList.add("hidden");
        }
    });

    checkEligibilityButton.addEventListener("click", () => {
        const regNo = regNoInput.value.trim();
        const courseName = courseNameInput.value.trim();
        if (!/^\d{12}$/.test(regNo)) return showError("Please enter a valid 12-digit register number.");
        if (!courseName) return showError("Please enter a course name.");
        showError("");
        fetchStudentDetails(regNo, courseName);
    });
});