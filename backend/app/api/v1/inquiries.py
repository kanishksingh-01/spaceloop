from flask import Blueprint, jsonify
inquiries_bp = Blueprint('inquiries', __name__)

@inquiries_bp.route('/ping', methods=['GET'])
def ping_inquiries():
    return jsonify({'module': 'inquiries', 'status': 'online'})
