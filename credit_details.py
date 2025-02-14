from flask import Blueprint, request, render_template, jsonify
import pandas as pd
import os

credit_details_bp = Blueprint('credit_details', __name__)

# File Paths
CREDITS_FILE = os.path.join(os.getcwd(), "data", "credits.xlsx")
STUDENT_DETAILS_FILE = os.path.join(os.getcwd(), "data", "student_credits.xlsx")
CURRICULUM_FILE = os.path.join(os.getcwd(), "data", "curriculum.xlsx")

DEPARTMENT_MAPPINGS_stu = {
    "23": "Artificial Intelligence and Data Science (AI&DS)",
    "24": "Artificial Intelligence and Machine Learning (AIML)",
    "10": "CSE (Cyber Security)",
    "11": "CSE (Internet of Things)",
    "01": "Computer Science and Engineering",
    "22": "Information Technology"
}

# Department mappings for sheets
DEPARTMENT_MAPPINGS = {
    "23": "aids_courses",
    "24": "aiml",
    "10": "CSE (Cyber Security)",
    "11": "CSE (Internet of Things)",
    "01": "Computer Science and Engineering",
    "22": "Information Technology"
}

# Curriculum Sheet Mapping
CURRICULUM_SHEET_MAPPING = {
    "23": "R2019-AI&DS",
    "24": "AIML",
    "10": "CSE(CS)",
    "11": "CSE(IOT)",
    "01": "CSE",
    "22": "IT"
}

# Sheet Mapping for Credit Requirements
CREDIT_SHEET_MAPPING = {
    21: "credit_details 19-1",
    22: "credit details 19-2",
    23: "credit details 19-2",
    24: "credit details 24"
}

# Mapping Department Code to Column Name in `credits.xlsx`
CREDIT_DEPARTMENT_MAPPING = {
    "23": "AIDS",
    "24": "AIML",
    "10": "CSC",
    "11": "IOT",
    "01": "CS",
    "22": "IT"
}

def get_student_details(reg_no):
    """Extracts student department, year, and regulation from register number."""
    if len(reg_no) != 12 or not reg_no.isdigit():
        return None

    join_year = int(reg_no[4:6])
    department_code = reg_no[6:8]
    regulation = "R2019" if join_year <= 23 else "R2024"
    department = DEPARTMENT_MAPPINGS_stu.get(department_code, "Unknown Department")

    current_year = (2025 % 100) - join_year + 1
    student_year = f"{current_year}{['th', 'st', 'nd', 'rd'][min(current_year, 3)]} Year" if 1 <= current_year <= 4 else "Graduated"

    return {
        "reg_no": reg_no,
        "department": department,
        "student_year": student_year,
        "regulation": regulation,
        "department_code": department_code
    }

def get_total_credit_info(department_code, join_year):
    """Fetches total credit requirements for the student's department."""
    if not os.path.exists(CREDITS_FILE):
        print("[ERROR] Credits file not found")
        return None

    sheet_name = CREDIT_SHEET_MAPPING.get(join_year, "credit details 24")

    try:
        df = pd.read_excel(CREDITS_FILE, sheet_name=sheet_name)
        df.columns = df.columns.str.strip().str.upper()

        if "CATEGORY" not in df.columns:
            print(f"[ERROR] 'CATEGORY' column not found in sheet '{sheet_name}'")
            return None

        department_key = CREDIT_DEPARTMENT_MAPPING.get(department_code, "").upper()
        if department_key not in df.columns:
            print(f"[ERROR] Department '{department_key}' not found in sheet '{sheet_name}'")
            return None

        credit_info = df[["CATEGORY", department_key]].to_dict(orient="records")
        total_credits_dict = {row["CATEGORY"]: row[department_key] for row in credit_info}

        return total_credits_dict
    except Exception as e:
        print(f"[ERROR] Unable to fetch total credits from '{sheet_name}': {e}")
        return None

def get_student_credit_info(reg_no, department_code):
    """Fetches student's completed courses and computes earned credits per category."""
    if not os.path.exists(STUDENT_DETAILS_FILE):
        print("[ERROR] Student details file not found")
        return None

    try:
        sheet_name = DEPARTMENT_MAPPINGS.get(department_code, "Unknown Department")
        df = pd.read_excel(STUDENT_DETAILS_FILE, sheet_name=sheet_name)
        df.columns = df.columns.str.strip().str.upper()

        reg_col = next((col for col in df.columns if "REGISTER NUMBER" in col), None)
        if not reg_col:
            print("[ERROR] 'Register Number' column not found")
            return None

        df[reg_col] = df[reg_col].astype(str).str.strip()
        student_data = df[df[reg_col] == reg_no]

        if student_data.empty:
            print(f"[ERROR] No data found for Register Number: {reg_no}")
            return None

        completed_courses = student_data.iloc[0].drop([reg_col, "NAME"], errors="ignore").dropna().tolist()
        earned_credits = compute_earned_credits(completed_courses, department_code)

        return earned_credits
    except Exception as e:
        print(f"[ERROR] Unable to fetch student credit details: {e}")
        return None

def compute_earned_credits(completed_courses, department_code):
    """Computes earned credits per category and lists completed courses."""
    if not os.path.exists(CURRICULUM_FILE):
        print(f"[ERROR] Curriculum file not found at: {CURRICULUM_FILE}")
        return None

    sheet_name = CURRICULUM_SHEET_MAPPING.get(department_code)
    if not sheet_name:
        print(f"[ERROR] No sheet mapping found for department code: {department_code}")
        return None

    try:
        df = pd.read_excel(CURRICULUM_FILE, sheet_name=sheet_name, header=1)
        df.columns = df.columns.str.strip().str.upper()

        # Normalize course titles for comparison
        df["COURSE TITLE"] = df["COURSE TITLE"].str.strip().str.lower()
        cleaned_courses = [c.strip().lower() for cell in completed_courses if isinstance(cell, str) for c in cell.split(",")]

        # Filter courses that match completed ones
        df_filtered = df[df["COURSE TITLE"].isin(cleaned_courses)]
        df_filtered.loc[:, "TOTAL CREDITS"] = pd.to_numeric(df_filtered["TOTAL CREDITS"], errors='coerce').fillna(0)

        earned_credit_summary = df_filtered.groupby("CATEGORY")["TOTAL CREDITS"].sum().to_dict()
        completed_courses_by_category = df_filtered.groupby("CATEGORY")["COURSE TITLE"].apply(list).to_dict()

        # ✅ Keep category names as they are (BS, PC, etc.)
        normalized_credits = earned_credit_summary.copy()
        normalized_courses = completed_courses_by_category.copy()

        # Ensure all categories exist in the dictionary (even if they are 0)
        all_categories = ["BS", "EEC", "ES", "HS", "MC", "OE", "PC", "PE", "TOTAL"]
        for cat in all_categories:
            normalized_credits.setdefault(cat, 0)
            normalized_courses.setdefault(cat, [])

        # Calculate total credits
        normalized_credits["TOTAL"] = sum(v for k, v in normalized_credits.items() if k != "TOTAL")

        return {
            "earned_credits": normalized_credits,
            "completed_courses": normalized_courses
        }

    except Exception as e:
        print(f"[ERROR] Unable to read curriculum.xlsx: {e}")
        return None
    
@credit_details_bp.route('/credit_details', methods=['GET', 'POST'])
def credit_details():
    if request.method == "POST":
        reg_no = request.json.get("reg_no", "").strip()
        student_info = get_student_details(reg_no)

        if not student_info:
            return jsonify({"error": "Invalid Register Number"}), 400

        student_credit_info = get_student_credit_info(reg_no, student_info["department_code"])
        total_credit_info = get_total_credit_info(student_info["department_code"], int(reg_no[4:6]))
        completed_courses = student_credit_info["completed_courses"] if student_credit_info else {}

        return jsonify({
            "student_info": student_info,
            "total_credit_info": total_credit_info,
            "student_credit_info": student_credit_info["earned_credits"],
            "completed_courses": completed_courses
        })
    
    return render_template('credit_details.html')

@credit_details_bp.route('/get_completed_courses', methods=['POST'])
def get_completed_courses():
    try:
        data = request.json
        reg_no = data.get("reg_no")
        category = data.get("category")

        if not reg_no or not category:
            return jsonify({"error": "Missing register number or category"}), 400

        # Fetch student info
        student_info = get_student_details(reg_no)
        if not student_info:
            return jsonify({"error": "Invalid register number"}), 400

        department_code = student_info["department_code"]
        regulation = student_info["regulation"]  # Fetch student's regulation (R2019 or R2024)
        student_credit_info = get_student_credit_info(reg_no, department_code)

        if not student_credit_info:
            return jsonify({"error": "Student credit information not found"}), 404

        # Get completed courses for the given category
        completed_courses = student_credit_info.get("completed_courses", {}).get(category, [])

        # Validate department sheet
        curriculum_sheet = CURRICULUM_SHEET_MAPPING.get(department_code)
        
        if not curriculum_sheet:
            return jsonify({"error": "Curriculum sheet not found for department"}), 404

        # Read curriculum data
        curriculum_df = pd.read_excel(CURRICULUM_FILE, sheet_name=curriculum_sheet, header=1)
        curriculum_df.columns = curriculum_df.columns.str.strip()
        curriculum_df = curriculum_df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        # Determine correct Course Code column based on regulation
        course_code_column = "Course Code R2019" if regulation == "R2019" else "Course Code R2024"

        # Ensure required columns exist
        required_columns = {course_code_column, "Course Title", "Theory Credits", "Practical Credits", "Total Credits"}
        missing_columns = required_columns - set(curriculum_df.columns)
        if missing_columns:
            return jsonify({"error": f"Missing required columns in curriculum data: {missing_columns}"}), 500

        # Normalize course titles for matching
        curriculum_df["Course Title"] = curriculum_df["Course Title"].str.lower().str.strip()
        completed_courses = [course.lower().strip() for course in completed_courses]

        # Extract matching course details
        completed_course_details = curriculum_df[curriculum_df["Course Title"].isin(completed_courses)][
            [course_code_column, "Course Title",  "Theory Credits", "Practical Credits", "Total Credits"]
        ]

        # Rename course code column dynamically
        completed_course_details = completed_course_details.rename(columns={course_code_column: "Course Code"})

        # Replace NaN values with "N/A"
        completed_course_details = completed_course_details.fillna("N/A")  

        # Convert to JSON-friendly format
        completed_course_list = completed_course_details.to_dict(orient="records")

        return jsonify({
            "category": category,
            "courses": completed_course_list
        })

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
