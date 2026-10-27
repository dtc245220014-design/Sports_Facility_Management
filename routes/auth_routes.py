from flask import Blueprint, request, jsonify, session
from services.auth_service import authenticate_user

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """FR-01, FR-02: Đăng nhập phân quyền Admin / Staff"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Vui lòng nhập tên đăng nhập và mật khẩu"}), 400

    user, error = authenticate_user(username, password)
    if error:
        return jsonify({"success": False, "message": error}), 401

    session['user_id'] = user['id']
    session['username'] = user['username']
    session['role'] = user['role']

    return jsonify({
        "success": True,
        "message": f"Đăng nhập thành công với vai trò {user['role']}",
        "user": user
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Đã đăng xuất"})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 200
    return jsonify({
        "authenticated": True,
        "user": {
            "id": session.get('user_id'),
            "username": session.get('username'),
            "role": session.get('role')
        }
    })

