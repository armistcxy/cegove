from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
import jwt
from jwt import PyJWTError
from functools import wraps
import os

security = HTTPBearer()

class AuthMiddleware:
    """Middleware để xác thực và phân quyền"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
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
        email = payload.get("email")
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
    
    def require_role(self, allowed_roles: List[str]):
        """Decorator để kiểm tra role có được phép không"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Lấy credentials từ kwargs
                credentials = kwargs.get('credentials')
                if not credentials:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Thiếu token xác thực"
                    )
                
                user = self.get_current_user(credentials)
                
                if user["role"] not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Không có quyền. Yêu cầu role: {', '.join(allowed_roles)}"
                    )
                
                # Thêm user vào kwargs để sử dụng trong endpoint
                kwargs['current_user'] = user
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator


# Instance singleton
auth_middleware = AuthMiddleware()