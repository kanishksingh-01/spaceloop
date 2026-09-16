from flask import Blueprint, jsonify
payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/ping', methods=['GET'])
def ping_payments():
    return jsonify({'module': 'payments', 'status': 'online'})
