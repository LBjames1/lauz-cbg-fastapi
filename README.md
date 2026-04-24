# CBG FastAPI 后端项目

为H5小程序提供后端服务的FastAPI应用，支持MySQL数据库和MinIO对象存储，包含完整的用户认证系统。

## 技术栈

- **Web框架**: FastAPI 0.115.0
- **数据库**: MySQL + SQLAlchemy 2.0.34
- **对象存储**: MinIO 7.2.20
- **认证**: JWT (PyJWT + python-jose)
- **密码加密**: bcrypt + passlib
- **异步服务器**: uvicorn
- **数据验证**: Pydantic 2.9.2
- **数据库迁移**: Alembic

## 项目结构

```
cbg-fast-api/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI入口和应用配置
│   ├── config.py              # 环境变量配置管理
│   ├── database.py            # 数据库连接会话管理
│   ├── models.py              # SQLAlchemy数据模型（8个表）
│   ├── schemas.py             # Pydantic请求/响应模型
│   ├── minio_client.py        # MinIO客户端初始化
│   ├── routes/
│   │   ├── fabrics.py         # 布料管理接口（CRUD + 分页 + 搜索）
│   │   ├── projects.py        # 作品管理接口（CRUD + 分页 + 搜索）
│   │   ├── patterns.py        # 纸样管理接口（CRUD + 分页 + 搜索）
│   │   ├── items.py           # 物品管理接口（CRUD + 分页 + 搜索）
│   │   ├── codes.py           # 编码字典管理接口（材质/颜色/工艺等）
│   │   ├── upload.py          # 图片上传接口（统一图片表）
│   │   └── users.py           # 用户认证接口（注册/登录/信息管理）
│   └── utils/
│       ├── auth.py            # JWT认证和密码加密工具
│       ├── pagination.py      # 分页查询工具
│       ├── query_helpers.py   # 搜索过滤辅助函数
│       ├── image.py           # 图片处理工具（压缩/缩放）
│       └── schemas.py         # 通用响应模型
├── .env                       # 环境变量配置文件
├── requirements.txt           # Python依赖包列表
├── Dockerfile                 # Docker镜像构建文件
├── docker-compose.yml         # Docker Compose编排配置
├── deploy.sh                  # Linux一键部署脚本
├── manage.sh                  # Linux容器管理脚本
├── init_db.py                 # 数据库初始化脚本（创建表和默认管理员）
├── init_admin_user.py         # 初始化管理员用户脚本
├── health_check.py            # 健康检查脚本
├── DEPLOYMENT.md              # Docker部署详细指南
└── README.md                  # 项目说明文档
```

## 快速开始

### 1. 环境准备

确保已安装：
- Python 3.9+
- MySQL 5.7+ 或 8.0+
- Docker & Docker Compose（可选，用于容器化部署）
- MinIO服务（或使用外部MinIO）

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
复制并编辑 `.env` 文件，配置数据库、MinIO和JWT相关信息。

### 4. 初始化数据库
```bash
# 创建所有数据表和默认管理员账户（admin/admin123）
python init_db.py
```

### 5. 启动开发服务器
```bash
uvicorn app.main:app --reload
```

访问 http://localhost:8000/docs 查看API文档

### 6. 使用Docker部署（推荐生产环境）
```bash
# 首次部署：构建镜像并启动服务
docker-compose up -d --build

# 代码更新后重启容器
docker-compose restart

# 查看日志
docker-compose logs -f cbg-app

# 访问API文档
http://localhost:8000/docs
```

详细部署说明请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)

## 环境变量配置

在`.env`文件中配置：
- `DATABASE_URL`: MySQL数据库连接字符串
- `MINIO_ENDPOINT`: MinIO服务地址
- `MINIO_ACCESS_KEY`: MinIO访问密钥
- `MINIO_SECRET_KEY`: MinIO密钥
- `MINIO_BUCKET_NAME`: MinIO存储桶名称
- `SECRET_KEY`: JWT密钥
- `ALGORITHM`: JWT算法
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT过期时间

## 核心功能模块

### 1. 用户认证系统 (`/api/users`)
- **POST** `/users/register` - 用户注册（需要唯一用户名和邮箱）
- **POST** `/users/token` - 用户登录获取JWT令牌（OAuth2兼容）
- **GET** `/users/me` - 获取当前登录用户信息（需认证）
- **PUT** `/users/me` - 更新当前用户信息（需认证）
- **特性**: JWT认证、密码bcrypt加密、OAuth2标准

### 2. 布料管理 (`/api/fabrics`)
- **POST** `/fabrics` - 创建布料记录（关联材质、厚度、颜色编码）
- **GET** `/fabrics/{id}` - 获取布料详情（含关联图片和编码信息）
- **GET** `/fabrics` - 获取布料列表（支持分页、关键词搜索、编码过滤）
- **PUT** `/fabrics/{id}` - 更新布料信息
- **DELETE** `/fabrics/{id}` - 删除布料
- **字段**: 名称、购买渠道、价格、尺寸、描述、备注、材质/厚度/颜色编码、图片集

### 3. 作品管理 (`/api/projects`)
- **POST** `/projects` - 创建作品（关联纸样、类型、布料、工艺）
- **GET** `/projects/{id}` - 获取作品详情（含完整关联数据）
- **GET** `/projects` - 获取作品列表（支持分页、多条件搜索）
- **PUT** `/projects/{id}` - 更新作品信息
- **DELETE** `/projects/{id}` - 删除作品
- **字段**: 标题、创作日期、用途说明、备注、纸样、类型、布料集、工艺集、发布状态、图片集

### 4. 纸样管理 (`/api/patterns`)
- **POST** `/patterns` - 创建纸样（关联品类、款式编码）
- **GET** `/patterns/{id}` - 获取纸样详情（含关联图片和编码）
- **GET** `/patterns` - 获取纸样列表（支持分页、搜索、过滤）
- **PUT** `/patterns/{id}` - 更新纸样信息
- **DELETE** `/patterns/{id}` - 删除纸样
- **字段**: 名称、来源、备注、品类、款式集、图片集

### 5. 物品管理 (`/api/items`)
- **POST** `/items` - 创建物品（关联类型编码）
- **GET** `/items/{id}` - 获取物品详情（含关联图片和编码）
- **GET** `/items` - 获取物品列表（支持分页、搜索、过滤）
- **PUT** `/items/{id}` - 更新物品信息
- **DELETE** `/items/{id}` - 删除物品
- **字段**: 名称、购买渠道、价格、购买日期、备注、类型、图片集

### 6. 编码字典管理 (`/api/codes`)
统一的编码管理系统，支持多种业务场景的标准化数据：
- **POST** `/codes` - 创建编码条目
- **GET** `/codes/{id}` - 获取编码详情
- **GET** `/codes` - 获取编码列表（可按entity_type、code_type过滤）
- **PUT** `/codes/{id}` - 更新编码信息
- **DELETE** `/codes/{id}` - 删除编码
- **支持的编码类型**:
  - `material`: 材质（棉、麻、丝、毛等）
  - `color`: 颜色（红、蓝、绿等）
  - `thickness`: 厚度（薄、中、厚等）
  - `type`: 类型（服装、家居、配饰等）
  - `category`: 品类（上衣、裤子、裙子等）
  - `style`: 款式（简约、复古、现代等）
  - `technique`: 工艺（刺绣、印花、拼接等）

### 7. 图片上传与管理 (`/api/upload`)
基于MinIO的统一图片存储服务：
- **POST** `/images` - 上传图片到MinIO（支持自动压缩和缩放）
- **GET** `/images` - 获取指定实体的图片列表（按entity_type和entity_id）
- **PUT** `/images/{image_id}` - 更新图片信息（排序、描述、类型）
- **DELETE** `/images/{image_id}` - 删除图片（同时删除MinIO文件）
- **支持的实体类型**: fabric, project, pattern, item
- **图片类型**: cover（封面）、detail（详情）、normal（普通）
- **特性**: 自动压缩、尺寸限制、排序管理、MinIO持久化存储

## 高级特性

### 分页与搜索功能
所有列表接口均支持：
- **分页参数**: `page`（页码，默认1）、`page_size`（每页数量，默认10，最大100）
- **关键词搜索**: `keyword` - 模糊匹配名称/标题字段
- **编码过滤**: 通过query参数过滤关联的编码值（如 `?material_id=1&color_id=2`）
- **响应格式**: 标准化的分页响应 `{data: [], total: 0, page: 1, page_size: 10}`

### 关联数据加载
- 详情页自动加载所有关联数据（编码、图片、多对多关系）
- 列表页可选择性加载关联数据以优化性能
- 使用SQLAlchemy的joinedload和selectinload优化查询

### 数据模型设计
- **8个核心数据表**: users, fabrics, projects, patterns, items, codes, images, 及4个关联表
- **统一图片表**: images表统一管理所有实体的图片，避免冗余设计
- **编码字典化**: 使用codes表标准化材质、颜色等枚举值，便于维护和扩展
- **多对多关系**: 通过关联表实现灵活的实体关联（布料-颜色、作品-布料等）
- **软删除**: 部分实体支持is_active标记实现逻辑删除