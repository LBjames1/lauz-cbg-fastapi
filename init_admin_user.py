"""初始化管理员用户脚本"""
from app.database import SessionLocal, engine, Base
from app.models import User
from app.utils.auth import get_password_hash

def init_admin_user():
    """创建初始管理员用户"""
    print("开始创建数据库表...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已存在 admin 用户
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("管理员用户已存在")
            return
        
        # 创建管理员用户
        hashed_password = get_password_hash("admin123")
        admin_user = User(
            username="admin",
            email="admin@example.com",
            phone="13800138000",
            full_name="系统管理员",
            nickname="Admin",
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✓ 管理员用户创建成功")
        print(f"  用户名：admin")
        print(f"  密码：admin123")
        print(f"  邮箱：admin@example.com")
        
    except Exception as e:
        print(f"✗ 创建失败：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_user()
