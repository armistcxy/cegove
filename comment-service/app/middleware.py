# ==================== comment-service/app/middleware.py ====================
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
import jwt
from jwt import PyJWTError
from functools import wraps
from app.config import settings

security = HTTPBearer()


class AuthMiddleware:
    """Middleware để xác thực và phân quyền"""
    
    def __init__(self):
        # Load JWT secret from config (loaded from Consul)
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
    
    def decode_token(self, token: str) -> dict:
        """Giải mã JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ hoặc đã hết hạn"
            )
    
    def verify_token(self, credentials: HTTPAuthorizationCredentials) -> dict:
        """Xác thực token từ header Authorization"""
        if credentials.scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sai định dạng authentication scheme"
            )
        
        token = credentials.credentials
        return self.decode_token(token)
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials):
        """Lấy thông tin user hiện tại từ token"""
        payload = self.verify_token(credentials)
        user_id = payload.get("userId")
        email = payload.get("sub")
        role = payload.get("role")
        
        if not user_id or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token thiếu thông tin"
            )
        
        return {
            "user_id": user_id,
            "email": email,
            "role": role
        }


# Instance singleton
auth_middleware = AuthMiddleware()