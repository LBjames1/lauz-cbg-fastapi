from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 统一响应模型
class ApiResponse(BaseModel):
    code: int = 200
    message: str = ""
    data: Any = None

# 登录相关Schema
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# 编码类 Schema (提前定义以避免循环引用)
class CodeBase(BaseModel):
    entity_type: str
    entity_type_name: Optional[str] = None
    code_type: str
    code_type_name: Optional[str] = None
    code_value: str
    display_name: str
    sort_order: Optional[int] = 0

class CodeCreate(CodeBase):
    pass

class CodeUpdate(CodeBase):
    pass

class CodeResponse(CodeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 图片相关Schema
class ImageBase(BaseModel):
    image_url: str
    image_type: Optional[str] = "normal"  # cover, detail, normal
    sort_order: Optional[int] = 0
    description: Optional[str] = None
    entity_type: Optional[str] = None  # fabric, project, pattern, item
    entity_id: Optional[int] = None

class ImageCreate(ImageBase):
    pass

class ImageUpdate(ImageBase):
    pass

class ImageResponse(ImageBase):
    id: int
    entity_type: str
    entity_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 简化的图片关联Schema
class ImageId(BaseModel):
    id: int
    image_type: Optional[str] = "normal"
    sort_order: Optional[int] = 0
    description: Optional[str] = None

# 布料相关Schema
class FabricBase(BaseModel):
    name: str
    purchase_channel: Optional[str] = None
    price: Optional[int] = 0
    purchase_date: Optional[datetime] = None
    width: Optional[str] = None
    length: Optional[str] = None  # 长度
    description: Optional[str] = None
    remark: Optional[str] = None
    
    # 编码字段
    material_id: Optional[int] = None
    thickness_id: Optional[int] = None
    color_ids: Optional[List[int]] = None

class FabricCreate(FabricBase):
    image_ids: Optional[List[ImageId]] = None

class FabricUpdate(FabricBase):
    image_ids: Optional[List[ImageId]] = None

class FabricResponse(FabricBase):
    id: int
    # 关联的编码信息
    material: Optional[CodeResponse] = None
    thickness: Optional[CodeResponse] = None
    colors: Optional[List[CodeResponse]] = None
    # 关联的图片信息
    images: Optional[List[ImageResponse]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 作品相关Schema
class ProjectBase(BaseModel):
    title: str
    creation_date: Optional[datetime] = None
    purpose_description: Optional[str] = None
    remark: Optional[str] = None
    
    # 编码字段
    pattern_id: Optional[int] = None
    type_id: Optional[int] = None
    fabric_ids: Optional[List[int]] = None
    technique_ids: Optional[List[int]] = None

class ProjectCreate(ProjectBase):
    image_ids: Optional[List[ImageId]] = None

class ProjectUpdate(ProjectBase):
    image_ids: Optional[List[ImageId]] = None

class ProjectResponse(ProjectBase):
    id: int
    # 关联的编码信息
    pattern: Optional[CodeResponse] = None
    type: Optional[CodeResponse] = None
    techniques: Optional[List[CodeResponse]] = None
    # 关联的图片信息
    images: Optional[List[ImageResponse]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 纸样相关Schema
class PatternBase(BaseModel):
    name: str
    source: Optional[str] = None
    remark: Optional[str] = None
    
    # 编码字段
    category_id: Optional[int] = None
    style_ids: Optional[List[int]] = None

class PatternCreate(PatternBase):
    image_ids: Optional[List[ImageId]] = None

class PatternUpdate(PatternBase):
    image_ids: Optional[List[ImageId]] = None

class PatternResponse(PatternBase):
    id: int
    # 关联的编码信息
    category: Optional[CodeResponse] = None
    styles: Optional[List[CodeResponse]] = None
    # 关联的图片信息
    images: Optional[List[ImageResponse]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 物品相关Schema
class ItemBase(BaseModel):
    name: str
    purchase_channel: Optional[str] = None
    price: Optional[int] = 0
    purchase_date: Optional[datetime] = None
    remark: Optional[str] = None
    
    # 编码字段
    type_id: Optional[int] = None

class ItemCreate(ItemBase):
    image_ids: Optional[List[ImageId]] = None

class ItemUpdate(ItemBase):
    image_ids: Optional[List[ImageId]] = None

class ItemResponse(ItemBase):
    id: int
    # 关联的编码信息
    type: Optional[CodeResponse] = None
    # 关联的图片信息
    images: Optional[List[ImageResponse]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 用户相关 Schema（已包含完整字段）
class UserBase(BaseModel):
    username: str
    email: str
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True