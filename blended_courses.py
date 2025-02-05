from flask import Blueprint

blended_courses_bp = Blueprint('blended_courses', __name__)

@blended_courses_bp.route('/blended_courses')
def blended_courses():
    return "<h2>Blended Courses Page</h2>"
