from flask import Blueprint, request, render_template, jsonify
from datetime import datetime
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process 

online_courses_bp = Blueprint('online_courses', __name__)

# Department mappings
DEPARTMENT_MAPPINGS = {
    "23": "Artificial Intelligence and Data Science (AI&DS)",
    "24": "Artificial Intelligence and Machine Learning (AIML)",
    "10": "CSE (Cyber Security)",
    "11": "CSE (Internet of Things)",
    "01": "Computer Science and Engineering",
    "22": "Information Technology"
}

# Sheet mappings for departments and regulations
SHEET_MAPPINGS = {
    "23": "AIDS-PC",
    "24": "AIML-PC",
    "10": "CS-PC",
    "11": "IOT-PC",
    "01": {
        "R2019": "CSE-34-PC",
        "R2024": "CSE-12-PC"
    },
    "22": {
        "R2019": "IT-34-PC",
        "R2024": "IT-12-PC"
    }
}

EXCEL_PATH = os.path.join(os.getcwd(), "data", "updateddata3.xlsx")
MLDATA_PATH = os.path.join(os.getcwd(), "data", "mldata.xlsx")
print("Loading file from:", MLDATA_PATH)

if os.path.exists(MLDATA_PATH):
    print("File found!")
else:
    print("File not found!")

# Utility Functions
def get_student_year(admission_year):
    """Calculate student's current year of study based on admission year."""
    current_year = datetime.now().year % 100
    try:
        admission_year = int(admission_year)
        if admission_year < 10 or admission_year > current_year:
            return "Invalid Year"
    except ValueError:
        return "Invalid Year"

    student_year = current_year - admission_year + 1
    return f"{student_year}{['th', 'st', 'nd', 'rd'][min(student_year, 3)]} Year" if 1 <= student_year <= 4 else "Graduated"

def get_sheet_name(department_code, regulation):
    """Get the correct sheet name based on department code and regulation."""
    sheet_info = SHEET_MAPPINGS.get(department_code)
    if isinstance(sheet_info, str):
        return sheet_info
    elif isinstance(sheet_info, dict):
        return sheet_info.get(regulation)
    return None

def fetch_course_data(sheet_name, column_name):
    """Fetch course data from a specific sheet."""
    if not sheet_name:
        print(f"[ERROR] Invalid sheet name: {sheet_name}")
        return []
    
    if not os.path.exists(EXCEL_PATH):
        print("[ERROR] Excel file not found:", EXCEL_PATH)
        return []

    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        if column_name in df.columns:
            return df[column_name].dropna().str.strip().unique().tolist()
        else:
            print(f"[ERROR] Column '{column_name}' not found in sheet '{sheet_name}'.")
            return []
    except Exception as e:
        print(f"[ERROR] Error fetching data from sheet {sheet_name}: {e}")
        return []

def match_course_name(input_name):
    """Match course names using TF-IDF similarity and fuzzy matching."""
    try:
        df = pd.read_excel(MLDATA_PATH)
        df.columns = df.columns.str.strip()

        all_names = []
        course_lookup = {}

        for _, row in df.iterrows():
            standard_name = row['Standard Course Name']
            aliases = row['Aliases'].split(', ') if pd.notna(row['Aliases']) else []
            aliases1 = row['Aliases1'].split(', ') if pd.notna(row['Aliases1']) else []

            merged_aliases = list(set(aliases + aliases1))
            all_names.extend(merged_aliases)

            for alias in merged_aliases:
                if alias.strip() and alias.strip() not in course_lookup:
                    course_lookup[alias.strip()] = []
                course_lookup[alias.strip()].append(standard_name)

        if not all_names:
            return []

        # TF-IDF Cosine Similarity Matching
        vectorizer = TfidfVectorizer().fit_transform([input_name] + all_names)
        similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:])[0]

        # Lowered similarity threshold for broader matches
        ranked_results = sorted(
            [(all_names[i], similarity[i]) for i in range(len(similarity)) if similarity[i] >= 0.5],
            key=lambda x: x[1], reverse=True
        )

        matched_courses = []
        for alias, _ in ranked_results:
            matched_courses.extend(course_lookup.get(alias, []))

        # Fuzzy Matching (Handles typos & near-matches)
        fuzzy_matches = process.extract(input_name, all_names, limit=5, scorer=process.fuzz.partial_ratio)
        for alias, score in fuzzy_matches:
            if score > 60:  # Adjust threshold based on performance
                matched_courses.extend(course_lookup.get(alias, []))

        return list(set(matched_courses))  # Remove duplicates

    except Exception as e:
        print(f"[ERROR] Error in matching course names: {e}")
        return []

def check_course_eligibility(reg_no, course_name):
    """Check if a student is eligible for a given course, considering aliases and fuzzy matching."""
    if not (len(reg_no) == 12 and reg_no.isdigit()):
        return "Invalid Register Number"

    department_code = reg_no[6:8]
    join_year = reg_no[4:6]
    regulation = "R2019" if int(join_year) <= 22 else "R2024"

    # Get department-specific sheet
    sheet_name = get_sheet_name(department_code, regulation)

    if not sheet_name:
        print(f"[ERROR] No sheet found for Department: {department_code}, Regulation: {regulation}")
        return "Unknown Eligibility"

    # Fetch department-specific courses
    dept_courses = fetch_course_data(sheet_name, "Course Title")
    
    if not dept_courses:
        return "Course data not available"

    # Load aliases from mldata.xlsx
    try:
        df = pd.read_excel(MLDATA_PATH)
        df.columns = df.columns.str.strip()

        alias_to_standard = {}  # Maps alias -> standard name
        standard_to_aliases = {}  # Maps standard name -> set of aliases

        for _, row in df.iterrows():
            standard_name = row['Standard Course Name'].strip().lower()
            aliases = row['Aliases'].split(', ') if pd.notna(row['Aliases']) else []
            aliases1 = row['Aliases1'].split(', ') if pd.notna(row['Aliases1']) else []
            
            all_aliases = set(aliases + aliases1)
            all_aliases.add(standard_name)  # Include standard name itself

            standard_to_aliases[standard_name] = all_aliases

            for alias in all_aliases:
                alias_to_standard[alias.lower()] = standard_name

    except Exception as e:
        print(f"[ERROR] Failed to load aliases: {e}")
        return "Error loading course data"

    # Normalize department sheet course names
    dept_courses_lower = {course.lower(): course for course in dept_courses}

    # Expand department courses with aliases
    expanded_dept_courses = set(dept_courses_lower.keys())  # Start with department courses
    for course in dept_courses_lower:
        if course in standard_to_aliases:
            expanded_dept_courses.update(standard_to_aliases[course])  # Add aliases for department courses

    # Normalize input course name
    course_name_lower = course_name.lower()
    
    # Fix: Ensure input course name is correctly mapped to the standard name
    matched_standard_name = alias_to_standard.get(course_name_lower, course_name_lower)

    print(f"[DEBUG] Input course: {course_name} → Matched Standard Name: {matched_standard_name}")

    # Use fuzzy matching to compare with department courses
    best_match, score = process.extractOne(matched_standard_name, expanded_dept_courses)

    print(f"[DEBUG] Best Fuzzy Match: {best_match} (Score: {score})")

    # If match score is high (e.g., above 85), consider it the same course
    if score >= 87:
        return "Not Eligible"

    return "Eligible"

@online_courses_bp.route('/online_courses', methods=['GET', 'POST'])
def online_courses():
    """Handle student details and course eligibility."""
    if request.method == 'POST':
        try:
            data = request.get_json()
            reg_no = data.get('reg_no', '').strip()
            course_name = data.get('course_name', '').strip()

            print(f"[DEBUG] Received reg_no: {reg_no}, course_name: {course_name}")

            if not (len(reg_no) == 12 and reg_no.isdigit()):
                return jsonify({"error": "Enter a valid 12-digit register number."}), 400

            join_year = reg_no[4:6]
            department_code = reg_no[6:8]

            student_year = get_student_year(join_year)
            regulation = "R2019" if int(join_year) <= 22 else "R2024"
            department = DEPARTMENT_MAPPINGS.get(department_code, "Unknown Department")

            response = {
                "reg_no": reg_no,
                "department": department,
                "student_year": student_year,
                "regulation": regulation
            }

            if course_name:
                eligibility = check_course_eligibility(reg_no, course_name)
                response.update({"eligibility": eligibility})
                
                if eligibility == "Eligible":
                    scoft_df = pd.read_excel(EXCEL_PATH, sheet_name="Online Courses(SCOFT)")
                    course_row = scoft_df[scoft_df['Course_Title'].str.lower() == course_name.lower()]
                    if not course_row.empty:
                        course_details = course_row.iloc[0].to_dict()
                        response.update({
                            "course_name": course_details.get('Course_Title', 'N/A'),
                            "platform": course_details.get('Platform', 'N/A'),
                            "course_code_R2019": course_details.get('Course Code R2019', 'N/A'),
                            "course_code_R2024": course_details.get('Course Code R2024', 'N/A'),
                            "credits": course_details.get('Credits', 'N/A'),
                            "duration": course_details.get('Course Duration    (Minimum 12 weeks)', 'N/A'),
                            "link": course_details.get('LINKS', 'N/A')
                        })

            print("[DEBUG] Response:", response)
            return jsonify(response)

        except Exception as e:
            print(f"[ERROR] Error in online_courses: {e}")
            return jsonify({"error": "An unexpected error occurred"}), 500

    return render_template('online_courses.html')

@online_courses_bp.route('/autocomplete', methods=['GET'])
def autocomplete():
    """Provide course name suggestions based on user input."""
    try:
        query = request.args.get('query', '').strip()
        print(f"[DEBUG] Autocomplete Query: {query}")

        if not query:
            return jsonify({"suggestions": []})

        suggestions = match_course_name(query)
        print(f"[DEBUG] Suggestions: {suggestions}")

        return jsonify({"suggestions": suggestions})

    except Exception as e:
        print(f"[ERROR] Error in autocomplete: {e}")
        return jsonify({"error": "Unable to fetch suggestions"}), 500