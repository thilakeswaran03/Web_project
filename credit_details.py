from flask import Blueprint, request, render_template, jsonify
import pandas as pd
import os

credit_details_bp = Blueprint('credit_details', __name__)

# File paths
CREDITS_FILE = os.path.join(os.getcwd(), "data", "credits.xlsx")
STUDENT_DETAILS_FILE = os.path.join(os.getcwd(), "data", "student_credits.xlsx")

# Department mappings
DEPARTMENT_MAPPINGS = {
    "23": "aids",
    "24": "aiml",
    "10": "CSE (Cyber Security)",
    "11": "CSE (Internet of Things)",
    "01": "Computer Science and Engineering",
    "22": "Information Technology"
}

def get_student_details(reg_no):
    """Extracts student department, year, and regulation from register number."""
    if len(reg_no) != 12 or not reg_no.isdigit():
        return None

    join_year = int(reg_no[4:6])
    department_code = reg_no[6:8]
    regulation = "R2019" if join_year <= 21 else "R2024"
    department = DEPARTMENT_MAPPINGS.get(department_code, "Unknown Department")

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
    """Fetches total credit requirements for the student's department from credits.xlsx."""
    if not os.path.exists(CREDITS_FILE):
        print("[ERROR] Credits file not found")
        return None

    # Determine the correct sheet based on joining year
    if join_year == 21:
        sheet_name = "credit_details 19-1"
    elif join_year in [22, 23]:
        sheet_name = "credit details 19-2"
    else:
        sheet_name = "credit details 24"

    try:
        df = pd.read_excel(CREDITS_FILE, sheet_name=sheet_name)

        # Normalize column names (strip spaces & convert to uppercase)
        df.columns = df.columns.str.strip().str.upper()
        print("[DEBUG] Available Columns:", df.columns.tolist())

        # Ensure 'CATEGORY' column exists
        if "CATEGORY" not in df.columns:
            print(f"[ERROR] 'CATEGORY' column not found in sheet '{sheet_name}'")
            return None

        # Mapping department code to correct sheet column
        department_mapping = {
            "23": "AIDS",
            "24": "AIML",
            "10": "CSC",  # Cyber Security
            "11": "IOT",  # Internet of Things
            "01": "CS",   # CSE
            "22": "IT"    # Information Technology
        }

        department_key = department_mapping.get(department_code, "").upper()

        if department_key not in df.columns:
            print(f"[ERROR] Department '{department_key}' not found in sheet '{sheet_name}'")
            return None

        # Extract category-wise credits for that department
        credit_info = df[["CATEGORY", department_key]].to_dict(orient="records")

        # Convert list of dicts into a dictionary for easy lookup in JS
        total_credits_dict = {row["CATEGORY"]: row[department_key] for row in credit_info}

        return total_credits_dict
    except Exception as e:
        print(f"[ERROR] Unable to fetch total credits from '{sheet_name}': {e}")
        return None

def get_student_credit_info(reg_no, department_code):
    """Fetches student's earned credits from the respective department sheet in student_details.xlsx."""
    if not os.path.exists(STUDENT_DETAILS_FILE):
        print("[ERROR] Student details file not found")
        return None

    try:
        excel_file = pd.ExcelFile(STUDENT_DETAILS_FILE)
        print(f"[DEBUG] Available Sheets: {excel_file.sheet_names}")

        sheet_name = DEPARTMENT_MAPPINGS.get(department_code, "Unknown Department")
        if sheet_name not in excel_file.sheet_names:
            print(f"[ERROR] Sheet '{sheet_name}' not found in Excel")
            return None

        df = pd.read_excel(STUDENT_DETAILS_FILE, sheet_name=sheet_name)
        df.columns = df.columns.str.strip().str.upper()  # Normalize column names to uppercase

        correct_column = next((col for col in df.columns if "REGISTER" in col), None)
        if not correct_column:
            print("[ERROR] 'Register Number' column not found")
            return None

        df[correct_column] = df[correct_column].astype(str).str.strip()
        student_data = df[df[correct_column] == reg_no]

        if student_data.empty:
            print(f"[ERROR] No data found for Register Number: {reg_no}")
            return None

        student_details = student_data.iloc[0].to_dict()

        # Extracting Name and Credit Information
        name = student_details.get("NAME", "N/A")
        credit_info = {category: student_details.get(category, 0) for category in ["HS", "BS", "ES", "PC", "PE", "OE", "EEC", "MC", "TOTAL"]}
        credit_info["name"] = name

        return credit_info
    except Exception as e:
        print(f"[ERROR] Unable to fetch student credit details: {e}")
        return None

@credit_details_bp.route('/credit_details', methods=['GET', 'POST'])
def credit_details():
    """Handles credit details page and student data retrieval."""
    if request.method == 'POST':
        reg_no = request.json.get("reg_no", "").strip()
        student_info = get_student_details(reg_no)

        if not student_info:
            return jsonify({"error": "Invalid Register Number"}), 400

        student_credit_info = get_student_credit_info(reg_no, student_info["department_code"])
        if not student_credit_info:
            return jsonify({"error": "Credit details not found"}), 404

        total_credit_info = get_total_credit_info(student_info["department_code"], int(reg_no[4:6]))
        if not total_credit_info:
            return jsonify({"error": "Total credit details not found"}), 404

        return jsonify({
            "student_info": student_info,
            "student_credit_info": student_credit_info,
            "total_credit_info": total_credit_info
        })

    return render_template('credit_details.html')
