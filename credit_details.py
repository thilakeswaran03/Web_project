from flask import Blueprint

credit_details_bp = Blueprint('credit_details', __name__)

@credit_details_bp.route('/credit_details')
def credit_details():
    return "<h2>Credit Details Page</h2>"
