from fastapi import FastAPI
from .config import settings
from .routes import fabrics, projects, upload, users, codes, patterns, items
from .utils.image import init_minio_client

# 创建 FastAPI 应用实例
app = FastAPI(
    title="CBG H5 小程序后端",
    description="为 H5 小程序提供 API 服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置 OpenAPI tags
app.openapi_tags = [
    {"name": "布料管理", "description": "布料相关操作"},
    {"name": "作品管理", "description": "作品相关操作"},
    {"name": "图片上传", "description": "图片上传和管理"},
    {"name": "用户管理", "description": "用户注册、登录和信息管理"},
    {"name": "编码管理", "description": "编码字典管理"},
    {"name": "纸样管理", "description": "纸样相关操作"},
    {"name": "物品管理", "description": "物品相关操作"},
]

# 强制清除 OpenAPI schema 缓存
app.openapi_schema = None

# 初始化MinIO客户端
minio_client = init_minio_client()

# 包含路由
app.include_router(fabrics.router, prefix="/api/fabrics", tags=["布料管理"])
app.include_router(projects.router, prefix="/api/projects", tags=["作品管理"])
app.include_router(upload.router, prefix="/api/upload", tags=["图片上传"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(codes.router, prefix="/api/codes", tags=["编码管理"])
app.include_router(patterns.router, prefix="/api/patterns", tags=["纸样管理"])
app.include_router(items.router, prefix="/api/items", tags=["物品管理"])

# 添加分页和搜索功能的依赖
from fastapi import Query

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "CBG FastAPI backend is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )