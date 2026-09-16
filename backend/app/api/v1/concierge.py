from flask import Blueprint, jsonify
concierge_bp = Blueprint('concierge', __name__)

@concierge_bp.route('/ping', methods=['GET'])
def ping_concierge():
    return jsonify({'module': 'concierge', 'status': 'online'})
