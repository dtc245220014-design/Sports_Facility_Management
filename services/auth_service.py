from extensions import db
from models.models import User

def authenticate_user(username, password):
    """
    Xác thực tài khoản và trả về thông tin User nếu đúng mật khẩu (BCrypt)
    """
    user = User.query.filter_by(username=username).first()
    if not user:
        return None, "Tên đăng nhập không tồn tại!"
    
    if not user.check_password(password):
        return None, "Mật khẩu không chính xác!"
    
    return user.to_dict(), None

def get_user_by_id(user_id):
    user = User.query.get(user_id)
    return user.to_dict() if user else None

