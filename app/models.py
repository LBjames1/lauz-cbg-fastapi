from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Fabric(Base):
    """布料模型"""
    __tablename__ = "fabrics"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    purchase_channel = Column(String(200))
    price = Column(Integer, default=0)
    purchase_date = Column(DateTime)
    width = Column(String(50))  # 幅宽
    length = Column(String(50))  # 长度
    description = Column(Text)
    remark = Column(Text)
    
    # 编码字段
    material_id = Column(Integer, ForeignKey("codes.id"))
    material = relationship("Code", foreign_keys=[material_id])
    
    thickness_id = Column(Integer, ForeignKey("codes.id"))
    thickness = relationship("Code", foreign_keys=[thickness_id])
    
    # 多对多关系 - 颜色
    colors = relationship("Code", secondary="fabric_colors")
    
    # 图片关系通过查询实现，避免复杂关系定义
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Project(Base):
    """作品模型"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    creation_date = Column(DateTime)
    purpose_description = Column(Text)
    remark = Column(Text)
    
    # 编码字段
    pattern_id = Column(Integer, ForeignKey("patterns.id"))
    pattern = relationship("Pattern")
    
    type_id = Column(Integer, ForeignKey("codes.id"))
    type = relationship("Code", foreign_keys=[type_id])
    
    # 多对多关系 - 布料
    fabrics = relationship("Fabric", secondary="project_fabrics")
    
    # 多对多关系 - 工艺
    techniques = relationship("Code", secondary="project_techniques")
    
    # 图片关系通过查询实现，避免复杂关系定义
    
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Pattern(Base):
    """纸样模型"""
    __tablename__ = "patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    source = Column(String(200))
    remark = Column(Text)
    
    # 编码字段
    category_id = Column(Integer, ForeignKey("codes.id"))
    category = relationship("Code", foreign_keys=[category_id])
    
    # 多对多关系 - 款式
    styles = relationship("Code", secondary="pattern_styles")
    
    # 图片关系通过查询实现，避免复杂关系定义
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Item(Base):
    """物品模型"""
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    purchase_channel = Column(String(200))
    price = Column(Integer, default=0)
    purchase_date = Column(DateTime)
    remark = Column(Text)
    
    # 编码字段
    type_id = Column(Integer, ForeignKey("codes.id"))
    type = relationship("Code", foreign_keys=[type_id])
    
    # 图片关系通过查询实现，避免复杂关系定义
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Code(Base):
    """编码类 - 用于材质、颜色、厚度、类型、品类、款式、工艺等"""
    __tablename__ = "codes"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), index=True)  # 实体类型 (fabric/project/pattern/item)
    entity_type_name = Column(String(100))  # 实体类型名称
    code_type = Column(String(50), index=True)  # 类型：material, color, thickness, type, category, style, technique
    code_type_name = Column(String(100))  # 编码类型名称
    code_value = Column(String(100), index=True)  # 编码值
    display_name = Column(String(100))  # 显示名称
    sort_order = Column(Integer, default=0)  # 排序
    
    # 关系可以通过查询实现
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# 多对多关联表
class FabricColor(Base):
    """布料-颜色关联表"""
    __tablename__ = "fabric_colors"
    
    fabric_id = Column(Integer, ForeignKey("fabrics.id"), primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), primary_key=True)

class ProjectFabric(Base):
    """作品-布料关联表"""
    __tablename__ = "project_fabrics"
    
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    fabric_id = Column(Integer, ForeignKey("fabrics.id"), primary_key=True)

class ProjectTechnique(Base):
    """作品-工艺关联表"""
    __tablename__ = "project_techniques"
    
    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), primary_key=True)

class PatternStyle(Base):
    """纸样-款式关联表"""
    __tablename__ = "pattern_styles"
    
    pattern_id = Column(Integer, ForeignKey("patterns.id"), primary_key=True)
    code_id = Column(Integer, ForeignKey("codes.id"), primary_key=True)

# 统一图片模型
class Image(Base):
    """统一图片模型 - 支持所有实体的图片管理"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(20), nullable=True)  # fabric, project, pattern, item（可选，支持临时上传）
    entity_id = Column(Integer, nullable=True)       # 关联的实体ID（可选）
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(20), default="normal")  # cover, detail, normal
    sort_order = Column(Integer, default=0)  # 排序
    description = Column(String(200))  # 描述
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# 用户模型
class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20))
    nickname = Column(String(50))
    avatar_url = Column(String(500))
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())