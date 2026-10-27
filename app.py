import os
import sys
from flask import Flask, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Khởi tạo db từ extensions
from extensions import db

# Import các Blueprints
from routes.auth_routes import auth_bp
from routes.court_routes import court_bp
from routes.booking_routes import booking_bp
from routes.ai_routes import ai_bp
from routes.report_routes import report_bp
from services import rag_service

def create_app(test_config=None):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)

    # Cấu hình bảo mật và CSDL
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sports-facility-super-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'mysql+pymysql://root:280706@localhost/sports_facility_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if test_config:
        app.config.update(test_config)

    # Khởi tạo db với app
    db.init_app(app)

    # Đăng ký các Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(court_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(report_bp)

    # Route tương thích ngược cho chat
    @app.route('/api/chat', methods=['POST'])
    def legacy_chat():
        from flask import request
        data = request.get_json() or {}
        user_query = data.get('message', '')
        if not user_query:
            return jsonify({"error": "Nội dung tin nhắn không được để trống"}), 400
        court_type = data.get('court_type')
        booking_date = data.get('date')
        reply = rag_service.process_chat_message(user_query, court_type, booking_date)
        return jsonify({"status": "success", "reply": reply})

    # Route giao diện người dùng chính
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "healthy", "service": "Sports Facility Management API with AI"})

    # Xử lý lỗi tập trung
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Endpoint không tồn tại"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"success": False, "message": "Lỗi máy chủ nội bộ"}), 500

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)