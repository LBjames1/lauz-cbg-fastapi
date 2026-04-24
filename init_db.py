from app.database import engine, Base
from sqlalchemy.orm import sessionmaker

def init_database():
    """初始化数据库表"""
    print("开始创建数据库表...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("数据库表创建完成！")
    
    # 添加初始编码数据
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # 创建编码类型
        code_types = [
            {"code_type": "material", "code_value": "cotton", "display_name": "棉"},
            {"code_type": "material", "code_value": "polyester", "display_name": "涤纶"},
            {"code_type": "material", "code_value": "wool", "display_name": "羊毛"},
            {"code_type": "color", "code_value": "red", "display_name": "红色"},
            {"code_type": "color", "code_value": "blue", "display_name": "蓝色"},
            {"code_type": "color", "code_value": "green", "display_name": "绿色"},
            {"code_type": "thickness", "code_value": "thin", "display_name": "薄"},
            {"code_type": "thickness", "code_value": "medium", "display_name": "中等"},
            {"code_type": "thickness", "code_value": "thick", "display_name": "厚"},
            {"code_type": "type", "code_value": "clothing", "display_name": "服装"},
            {"code_type": "type", "code_value": "home", "display_name": "家居"},
            {"code_type": "category", "code_value": "shirt", "display_name": "衬衫"},
            {"code_type": "category", "code_value": "dress", "display_name": "连衣裙"},
            {"code_type": "style", "code_value": "v-neck", "display_name": "V领"},
            {"code_type": "style", "code_value": "round-neck", "display_name": "圆领"},
            {"code_type": "technique", "code_value": "sewing", "display_name": "缝纫"},
            {"code_type": "technique", "code_value": "embroidery", "display_name": "刺绣"},
            {"code_type": "type", "code_value": "tool", "display_name": "工具"},
            {"code_type": "type", "code_value": "accessory", "display_name": "配饰"},
        ]
        
        # 延迟导入Code模型
        from app.models import Code
        for code_data in code_types:
            existing_code = db.query(Code).filter(
                Code.code_type == code_data["code_type"],
                Code.code_value == code_data["code_value"]
            ).first()
            if not existing_code:
                code = Code(**code_data)
                db.add(code)
        db.commit()
        print("已创建初始编码数据")
        
        # 创建超级管理员用户（可选）
        # 暂时跳过管理员创建以避免bcrypt问题
        print("跳过管理员用户创建，稍后可通过API创建")
    finally:
        db.close()

if __name__ == "__main__":
    init_database()