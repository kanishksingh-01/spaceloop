from flask import Blueprint, jsonify
inspections_bp = Blueprint('inspections', __name__)

@inspections_bp.route('/ping', methods=['GET'])
def ping_inspections():
    return jsonify({'module': 'inspections', 'status': 'online'})
