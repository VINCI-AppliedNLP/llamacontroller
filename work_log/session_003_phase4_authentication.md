# LlamaController 实施日志 - Session 003: Phase 4 认证系统

## 日期
2025-11-12

## 目标
实现 Phase 4: Authentication (认证系统)，包括数据库设计、用户认证、API 令牌系统和安全控制

## Phase 4: Authentication - 进行中

### 待办事项
- [ ] 设计数据库架构（SQLite）
  - [ ] 用户表
  - [ ] API 令牌表
  - [ ] 会话表
  - [ ] 操作日志表
- [ ] 实现数据库层
  - [ ] SQLAlchemy 模型
  - [ ] 数据库初始化脚本
  - [ ] CRUD 操作
- [ ] 实现用户认证
  - [ ] 密码哈希（bcrypt）
  - [ ] 登录端点
  - [ ] 会话管理
  - [ ] 登出端点
- [ ] 实现 API 令牌系统
  - [ ] 令牌生成
  - [ ] 令牌验证中间件
  - [ ] 令牌 CRUD 操作
  - [ ] 令牌过期处理
- [ ] 实现安全控制
  - [ ] 速率限制
  - [ ] 登录失败锁定
  - [ ] CSRF 保护
- [ ] 集成认证到现有端点
  - [ ] 保护管理端点
  - [ ] Ollama API 令牌验证
- [ ] 编写安全测试
  - [ ] 认证测试
  - [ ] 授权测试
  - [ ] 安全测试

## 实施计划

### 1. 数据库设计

#### 用户表 (users)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| username | VARCHAR(50) | 用户名，唯一 |
| password_hash | VARCHAR(255) | 密码哈希 |
| role | VARCHAR(20) | 角色：admin, user |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| is_active | BOOLEAN | 是否激活 |
| failed_login_attempts | INTEGER | 失败登录次数 |
| locked_until | DATETIME | 锁定到期时间 |

#### API 令牌表 (api_tokens)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 外键 -> users.id |
| token_hash | VARCHAR(255) | 令牌哈希 |
| name | VARCHAR(100) | 令牌名称 |
| created_at | DATETIME | 创建时间 |
| last_used_at | DATETIME | 最后使用时间 |
| expires_at | DATETIME | 过期时间（可选）|
| is_active | BOOLEAN | 是否激活 |

#### 会话表 (sessions)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| session_id | VARCHAR(255) | 会话 ID，唯一 |
| user_id | INTEGER | 外键 -> users.id |
| created_at | DATETIME | 创建时间 |
| expires_at | DATETIME | 过期时间 |
| ip_address | VARCHAR(45) | IP 地址 |
| user_agent | TEXT | 用户代理 |

#### 操作日志表 (audit_logs)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 外键 -> users.id（可选）|
| action | VARCHAR(50) | 操作类型 |
| resource | VARCHAR(100) | 资源 |
| details | TEXT | 详情（JSON）|
| ip_address | VARCHAR(45) | IP 地址 |
| created_at | DATETIME | 创建时间 |
| success | BOOLEAN | 是否成功 |

### 2. 技术栈
- **ORM**: SQLAlchemy 2.0
- **密码哈希**: bcrypt
- **令牌**: secrets.token_urlsafe
- **会话**: 服务器端会话（数据库）
- **数据库迁移**: Alembic

### 3. API 端点

#### 认证端点
- POST /api/v1/auth/login - 用户登录
- POST /api/v1/auth/logout - 用户登出
- GET /api/v1/auth/me - 获取当前用户信息
- POST /api/v1/auth/change-password - 修改密码

#### 令牌管理端点
- GET /api/v1/tokens - 列出当前用户的令牌
- POST /api/v1/tokens - 创建新令牌
- DELETE /api/v1/tokens/{token_id} - 删除令牌
- PATCH /api/v1/tokens/{token_id} - 更新令牌（激活/停用）

#### 用户管理端点（管理员）
- GET /api/v1/users - 列出所有用户
- POST /api/v1/users - 创建用户
- GET /api/v1/users/{user_id} - 获取用户信息
- PATCH /api/v1/users/{user_id} - 更新用户
- DELETE /api/v1/users/{user_id} - 删除用户

### 4. 安全措施
- ✅ 密码使用 bcrypt 哈希（cost factor 12）
- ✅ API 令牌使用 SHA-256 哈希存储
- ✅ 会话超时配置（默认 1 小时）
- ✅ 登录失败锁定（5 次失败锁定 5 分钟）
- ✅ HTTPS 强制（生产环境）
- ✅ CSRF 保护（Web UI）
- ✅ 速率限制（API 端点）

## 已完成
- [x] 创建会话日志文件
- [ ] 其他任务进行中...

## 下一步
1. 创建数据库模型
2. 实现认证服务
3. 创建认证端点
4. 集成到现有 API
5. 编写测试

## 注意事项
- 初始管理员账户从配置文件读取
- 令牌前缀 "llc_" 便于识别
- 审计日志记录所有关键操作
- 支持多用户和多令牌

## 文件清单（计划）
1. `src/llamacontroller/db/models.py` - 数据库模型
2. `src/llamacontroller/db/crud.py` - CRUD 操作
3. `src/llamacontroller/db/base.py` - 数据库基础设置
4. `src/llamacontroller/auth/service.py` - 认证服务
5. `src/llamacontroller/auth/utils.py` - 密码哈希等工具
6. `src/llamacontroller/auth/dependencies.py` - FastAPI 依赖
7. `src/llamacontroller/api/auth.py` - 认证端点
8. `src/llamacontroller/api/tokens.py` - 令牌管理端点
9. `src/llamacontroller/api/users.py` - 用户管理端点
10. `scripts/init_db.py` - 数据库初始化脚本
11. `scripts/create_admin.py` - 创建管理员脚本
12. `tests/test_auth.py` - 认证测试
