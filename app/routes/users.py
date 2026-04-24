from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserUpdate, UserResponse, ApiResponse
from ..utils.auth import get_password_hash, create_access_token, get_current_active_user, verify_password
from ..config import settings
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # 检查邮箱是否已存在
    db_email = db.query(User).filter(User.email == user.email).first()
    if db_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    user_response = UserResponse.model_validate(db_user)
    return {
        "code": 201,
        "message": "User registered successfully",
        "data": user_response
    }

@router.post("/token", response_model=ApiResponse)
def login_for_access_token(
    username: str = Body(..., embed=True), 
    password: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """用户登录获取令牌"""
    # 验证用户
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证密码
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成 token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # 转换为响应格式
    user_response = UserResponse.model_validate(user)
    return {
        "code": 200,
        "message": "Login successful",
        "data": {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
    }

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password", response_model=ApiResponse)
def change_password(
    password_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改用户密码"""
    # 验证旧密码
    if not verify_password(password_request.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )
    
    # 验证新密码长度（bcrypt限制）
    new_password_bytes = password_request.new_password.encode('utf-8')
    if len(new_password_bytes) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password is too long (maximum 72 characters)"
        )
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_request.new_password)
    db.commit()
    
    return {
        "code": 200,
        "message": "Password changed successfully",
        "data": None
    }

@router.post("/logout", response_model=ApiResponse)
def logout_user():
    """用户注销退出登录
    
    注意：这是一个JWT认证系统的注销接口
    - 服务器端不会保存token状态
    - 客户端需要清除本地存储的token
    - 前端实现建议：
      1. 清除localStorage/sessionStorage中的token
      2. 重定向到登录页面
      3. 清除用户相关信息
    """
    return {
        "code": 200,
        "message": "Logout successful",
        "data": None
    }

@router.get("/me", response_model=ApiResponse)
def read_users_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    user_response = UserResponse.model_validate(current_user)
    return {
        "code": 200,
        "message": "",
        "data": user_response
    }

@router.put("/me", response_model=ApiResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 更新用户信息
    for key, value in user_update.dict(exclude_unset=True).items():
        if key == "password":
            setattr(current_user, "hashed_password", get_password_hash(value))
        else:
            setattr(current_user, key, value)
    
    db.commit()
    db.refresh(current_user)
    # 将 SQLAlchemy 模型转换为 Pydantic 模型
    user_response = UserResponse.model_validate(current_user)
    return {
        "code": 200,
        "message": "User updated successfully",
        "data": user_response
    }

