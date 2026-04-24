"""通用查询工具函数"""
from sqlalchemy.orm import Session
from typing import List, Optional


def filter_by_code_type(query, model, db: Session, code_type: str, code_id: int, entity_type: str = None):
    """
    根据编码类型动态过滤查询
    
    Args:
        query: SQLAlchemy 查询对象
        model: 数据模型类
        db: 数据库会话
        code_type: 编码类型（如 fabric_material, fabric_color, project_type 等）- 与 /code-types接口返回值一致
        code_id: 编码 ID
        entity_type: 实体类型（fabric, project, pattern, item），用于多对多关系
        
    Returns:
        过滤后的查询对象
    """
    # 一对一关系字段映射（根据实际数据库 code_type 值）
    one_to_one_mapping = {
        # 布料 (fabric)
        'fabric_material': 'material_id',
        'fabric_thickness': 'thickness_id',
        
        # 作品 (project)
        'project_pattern': 'pattern_id',
        'project_type': 'type_id',
        
        # 纸样 (pattern)
        'pattern_category': 'category_id',
        
        # 物品 (item)
        'item_type': 'type_id',
    }
    
    # 多对多关系映射
    many_to_many_relations = {
        'fabric': {
            'fabric_color': ('FabricColor', 'fabric_id', 'code_id'),
        },
        'project': {
            'project_fabric': ('ProjectFabric', 'project_id', 'fabric_id'),
            'project_technique': ('ProjectTechnique', 'project_id', 'code_id'),
        },
        'pattern': {
            'pattern_style': ('PatternStyle', 'pattern_id', 'code_id'),
        }
    }
    
    # 处理一对一关系
    if code_type in one_to_one_mapping:
        field_name = one_to_one_mapping[code_type]
        if hasattr(model, field_name):
            return query.filter(getattr(model, field_name) == code_id)
    
    # 处理多对多关系
    if entity_type and entity_type in many_to_many_relations:
        relation_config = many_to_many_relations[entity_type].get(code_type)
        if relation_config:
            table_name, own_id_field, target_id_field = relation_config
            
            # 动态导入关联表
            from ..models import FabricColor, ProjectFabric, ProjectTechnique, PatternStyle
            relation_tables = {
                'FabricColor': FabricColor,
                'ProjectFabric': ProjectFabric,
                'ProjectTechnique': ProjectTechnique,
                'PatternStyle': PatternStyle
            }
            
            if table_name in relation_tables:
                relation_table = relation_tables[table_name]
                ids = db.query(getattr(relation_table, own_id_field)).filter(
                    getattr(relation_table, target_id_field) == code_id
                ).all()
                ids = [i[0] for i in ids]
                
                if ids:
                    return query.filter(getattr(model, 'id').in_(ids))
                else:
                    return query.filter(model.id == -1)
    
    return query


def filter_by_code_ids(query, model, db: Session, code_type: str, code_ids: List[int], entity_type: str = None):
    """
    根据编码 ID 列表动态过滤查询（支持多个 ID）
    
    Args:
        query: SQLAlchemy 查询对象
        model: 数据模型类
        db: 数据库会话
        code_type: 编码类型（如 fabric_color, project_fabric 等）- 与 /code-types接口返回值一致
        code_ids: 编码 ID 列表
        entity_type: 实体类型
        
    Returns:
        过滤后的查询对象
    """
    # 多对多关系映射
    many_to_many_relations = {
        'fabric': {
            'fabric_color': ('FabricColor', 'fabric_id', 'code_id'),
        },
        'project': {
            'project_fabric': ('ProjectFabric', 'project_id', 'fabric_id'),
            'project_technique': ('ProjectTechnique', 'project_id', 'code_id'),
        },
        'pattern': {
            'pattern_style': ('PatternStyle', 'pattern_id', 'code_id'),
        }
    }
    
    # 处理多对多关系
    if entity_type and entity_type in many_to_many_relations:
        relation_config = many_to_many_relations[entity_type].get(code_type)
        if relation_config:
            table_name, own_id_field, target_id_field = relation_config
            
            from ..models import FabricColor, ProjectFabric, ProjectTechnique, PatternStyle
            relation_tables = {
                'FabricColor': FabricColor,
                'ProjectFabric': ProjectFabric,
                'ProjectTechnique': ProjectTechnique,
                'PatternStyle': PatternStyle
            }
            
            if table_name in relation_tables:
                relation_table = relation_tables[table_name]
                ids = db.query(getattr(relation_table, own_id_field)).filter(
                    getattr(relation_table, target_id_field).in_(code_ids)
                ).all()
                ids = [i[0] for i in ids]
                
                if ids:
                    return query.filter(getattr(model, 'id').in_(ids))
                else:
                    return query.filter(model.id == -1)
    
    return query
