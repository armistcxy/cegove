from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.middleware import auth_middleware

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency để lấy user hiện tại"""
    return auth_middleware.get_current_user(credentials)


async def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency yêu cầu role admin"""
    if current_user["role"] not in ["SUPER_ADMIN", "LOCAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ admin mới có quyền truy cập"
        )
    return current_user


async def require_user(current_user: dict = Depends(get_current_user)):
    """Dependency yêu cầu role user hoặc cao hơn"""
    if current_user["role"] not in ["USER", "SUPER_ADMIN", "LOCAL_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu role user hoặc admin"
        )
    return current_user