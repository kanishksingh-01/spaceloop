from flask import Blueprint, jsonify
spaces_bp = Blueprint('spaces', __name__)

@spaces_bp.route('/ping', methods=['GET'])
def ping_spaces():
    return jsonify({'module': 'spaces', 'status': 'online'})
