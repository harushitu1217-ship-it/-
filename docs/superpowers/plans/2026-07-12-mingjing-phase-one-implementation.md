# 明景云端内容运营平台第一阶段 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有单机内容助手升级为可登录、可管理产品图片、可用多模型生成六平台内容、可审核并创建发布任务的云端第一阶段产品。

**Architecture:** 保留 React + TypeScript + Vite 和 FastAPI，先用 SQLAlchemy 建立可在 SQLite/PostgreSQL 间切换的数据层，再以 provider 接口隔离模型、图片、热点和平台发布能力。第一阶段的长任务使用数据库任务状态和同步执行器完成，接口边界保持可替换，以便后续接 Redis/Celery、对象存储和真实发布 API。

**Tech Stack:** React 19、TypeScript 6、Vite 8、FastAPI 0.116、Pydantic 2、SQLAlchemy 2、Alembic、PostgreSQL、SQLite、httpx、PyJWT、argon2-cffi、pytest、Vitest、Testing Library、Docker Compose。

## Global Constraints

- 品牌显示名称始终为“明景”，不得显示“明璟”。
- 只使用公开网页和官方接口，不绕过登录、验证码、付费墙或平台风控。
- 自动发布只使用官方开放接口或正式授权服务商；无授权时生成发布包并人工确认。
- AI 不得虚构资质、产能、价格、交期；未知事实返回“待确认”。
- 所有 AI 内容默认进入待审核状态。
- 豆包为默认模型；DeepSeek、通义千问和 OpenAI 作为可配置 provider。
- 文件上传仅允许 JPEG、PNG、WebP，单文件最大 10 MiB，单任务最多 9 张。
- 第一阶段本地允许 SQLite，正式部署使用 PostgreSQL。

---

## File Structure

- `backend/app/core/`：配置、密码、JWT、权限依赖。
- `backend/app/db/`：SQLAlchemy 会话、ORM 表和迁移入口。
- `backend/app/modules/auth/`：登录和用户管理。
- `backend/app/modules/catalog/`：公司、产品、素材和图片上传。
- `backend/app/modules/providers/`：模型、图片、热点和发布 provider 接口。
- `backend/app/modules/content/`：生成、质量检查、版本和审核状态。
- `backend/app/modules/publishing/`：发布任务和人工发布包。
- `backend/app/modules/trends/`：人工导入热点和模板结构。
- `frontend/src/features/`：按 auth、catalog、creation、review、publishing、settings 拆分页面和 API。
- `deploy/`：Dockerfile、Compose、环境变量样例和部署说明。

### Task 1: 建立可测试基线并修复中文品牌

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/seed_data.py`
- Modify: `backend/app/generator.py`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/Workspace.tsx`
- Modify: `frontend/src/data/platforms.ts`
- Test: `backend/tests/test_brand_copy.py`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Produces: UTF-8 中文界面；`BRAND_NAME = "明景"`；健康检查仍为 `GET /health`。

- [ ] **Step 1: 写失败的品牌测试**

```python
def test_bootstrap_uses_mingjing_brand(client):
    data = client.get("/api/bootstrap").json()
    assert data["company"]["name"].startswith("明景")
    assert "明璟" not in str(data)
```

```tsx
expect(await screen.findByRole("heading", { name: /明景内容运营助手/ })).toBeInTheDocument();
expect(screen.queryByText(/明璟/)).not.toBeInTheDocument();
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `python -m pytest backend/tests/test_brand_copy.py -v`
Expected: FAIL，因为当前品牌或中文字符串乱码。

Run: `pnpm --dir frontend test -- App.test.tsx`
Expected: FAIL，因为标题不是可读的“明景内容运营助手”。

- [ ] **Step 3: 将受影响源码按 UTF-8 重写并集中品牌常量**

```python
BRAND_NAME = "明景"
COMPANY_NAME = "明景绳带有限公司"
```

```tsx
<h1>明景内容运营助手</h1>
```

- [ ] **Step 4: 运行基线测试**

Run: `python -m pytest backend/tests -q`
Expected: PASS。

Run: `pnpm --dir frontend test && pnpm --dir frontend build`
Expected: PASS，且构建无 TypeScript 错误。

- [ ] **Step 5: 提交**

```bash
git add backend/app backend/tests frontend/src
git commit -m "fix: restore mingjing chinese copy"
```

### Task 2: 配置、SQLAlchemy 数据层和迁移

**Files:**
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_database_models.py`

**Interfaces:**
- Produces: `Settings.database_url: str`；`get_db()`；ORM 表 `users`, `company_profiles`, `products`, `assets`, `model_configs`, `content_jobs`, `content_versions`, `publish_tasks`, `trend_sources`, `audit_logs`。

- [ ] **Step 1: 写 SQLite 临时库迁移测试**

```python
def test_initial_schema_contains_core_tables(sqlite_engine):
    Base.metadata.create_all(sqlite_engine)
    names = set(inspect(sqlite_engine).get_table_names())
    assert {"users", "products", "assets", "content_jobs", "publish_tasks"} <= names
```

- [ ] **Step 2: 运行测试并确认模块不存在**

Run: `python -m pytest backend/tests/test_database_models.py -v`
Expected: FAIL with `ModuleNotFoundError: app.db`。

- [ ] **Step 3: 增加依赖与配置对象**

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/mingjing.db"
    jwt_secret: str = "development-only-change-me"
    upload_dir: Path = Path("data/uploads")
```

- [ ] **Step 4: 定义 ORM 和 Alembic 初始迁移**

```python
class ContentJob(Base):
    __tablename__ = "content_jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), default="draft")
    created_by_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
```

- [ ] **Step 5: 验证 SQLite 和迁移**

Run: `python -m pytest backend/tests/test_database_models.py -v`
Expected: PASS。

Run: `python -m alembic -c backend/alembic.ini upgrade head`
Expected: 创建全部初始表。

- [ ] **Step 6: 提交**

```bash
git add backend/app/core backend/app/db backend/alembic.ini backend/alembic backend/requirements.txt backend/tests/test_database_models.py
git commit -m "feat: add cloud-ready database foundation"
```

### Task 3: 用户认证与角色权限

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/modules/auth/schemas.py`
- Create: `backend/app/modules/auth/service.py`
- Create: `backend/app/modules/auth/routes.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `POST /api/auth/login`；`GET /api/auth/me`；`POST /api/users`；`require_roles(*roles)`。

- [ ] **Step 1: 写登录和权限失败测试**

```python
def test_operator_cannot_create_user(client, operator_token):
    response = client.post("/api/users", headers={"Authorization": f"Bearer {operator_token}"}, json={"username": "review", "password": "StrongPass123!", "role": "reviewer"})
    assert response.status_code == 403
```

- [ ] **Step 2: 运行并确认 404/失败**

Run: `python -m pytest backend/tests/test_auth.py -v`
Expected: FAIL，因为认证路由尚不存在。

- [ ] **Step 3: 实现 Argon2 密码和 JWT**

```python
def create_access_token(user_id: str, role: str, settings: Settings) -> str:
    return jwt.encode({"sub": user_id, "role": role, "exp": datetime.now(UTC) + timedelta(hours=8)}, settings.jwt_secret, algorithm="HS256")
```

- [ ] **Step 4: 实现三角色依赖和管理员初始化命令**

```python
Role = Literal["admin", "operator", "reviewer"]
```

Run: `python -m app.cli create-admin --username admin --password "StrongPass123!"`
Expected: 输出 `admin created`，重复执行输出 `admin already exists`。

- [ ] **Step 5: 运行认证测试**

Run: `python -m pytest backend/tests/test_auth.py -v`
Expected: PASS，覆盖正确登录、错误密码、过期令牌和 403。

- [ ] **Step 6: 提交**

```bash
git add backend/app/core/security.py backend/app/modules/auth backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add role-based authentication"
```

### Task 4: 公司、产品和安全图片素材

**Files:**
- Create: `backend/app/modules/catalog/schemas.py`
- Create: `backend/app/modules/catalog/service.py`
- Create: `backend/app/modules/catalog/routes.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_catalog.py`
- Test: `backend/tests/test_assets.py`

**Interfaces:**
- Produces: `GET/PUT /api/company-profile`；`GET/POST/PUT /api/products`；`POST /api/assets/images`；`DELETE /api/assets/{id}`。

- [ ] **Step 1: 写产品 CRUD 和上传限制测试**

```python
def test_rejects_image_larger_than_ten_mib(client, operator_token):
    response = client.post("/api/assets/images", headers=auth(operator_token), files={"file": ("large.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")})
    assert response.status_code == 413
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_catalog.py backend/tests/test_assets.py -v`
Expected: FAIL，因为路由或限制尚不存在。

- [ ] **Step 3: 实现资料 CRUD 和 MIME/大小/数量校验**

```python
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_JOB_IMAGES = 9
```

- [ ] **Step 4: 运行模块测试和路径穿越测试**

Run: `python -m pytest backend/tests/test_catalog.py backend/tests/test_assets.py -v`
Expected: PASS，上传文件名不会决定服务器路径。

- [ ] **Step 5: 提交**

```bash
git add backend/app/modules/catalog backend/app/main.py backend/tests/test_catalog.py backend/tests/test_assets.py
git commit -m "feat: add product catalog and secure assets"
```

### Task 5: 多模型 Provider、密钥加密和回退

**Files:**
- Create: `backend/app/modules/providers/base.py`
- Create: `backend/app/modules/providers/openai_compatible.py`
- Create: `backend/app/modules/providers/router.py`
- Create: `backend/app/modules/providers/crypto.py`
- Create: `backend/app/modules/providers/routes.py`
- Test: `backend/tests/test_model_router.py`
- Test: `backend/tests/test_model_config.py`

**Interfaces:**
- Produces: `ModelProvider.generate(request: ModelRequest) -> ModelResponse`；`ImageProvider.analyze(request) -> ImageAnalysis`；`ImageProvider.generate(request) -> GeneratedImage`；`ModelRouter.generate(request)`；`GET/PUT /api/settings/models`；`GET/PUT /api/settings/images`。

- [ ] **Step 1: 写主模型失败后回退测试**

```python
def test_router_falls_back_in_configured_order():
    router = ModelRouter([FailingProvider("doubao"), StubProvider("deepseek", "ok")])
    result = router.generate(ModelRequest(messages=[{"role": "user", "content": "test"}]))
    assert result.provider == "deepseek"
    assert result.text == "ok"
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_model_router.py backend/tests/test_model_config.py -v`
Expected: FAIL，因为 provider 层尚不存在。

- [ ] **Step 3: 实现 OpenAI-compatible 调用和四家配置映射**

```python
PROVIDER_DEFAULTS = {
    "doubao": "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
}
```

同时定义图片能力，未配置真实服务时返回明确的 `provider_not_configured`，不伪造图片：

```python
class ImageProvider(Protocol):
    def analyze(self, request: ImageAnalysisRequest) -> ImageAnalysis: ...
    def generate(self, request: ImageGenerationRequest) -> GeneratedImage: ...
```

- [ ] **Step 4: 加密保存密钥并只返回掩码**

```python
return {"provider": row.provider, "configured": bool(row.api_key_encrypted), "api_key_hint": "已保存" if row.api_key_encrypted else ""}
```

- [ ] **Step 5: 运行 provider 测试**

Run: `python -m pytest backend/tests/test_model_router.py backend/tests/test_model_config.py -v`
Expected: PASS，数据库和 API 响应不出现明文密钥，未配置图片服务时返回结构化错误。

- [ ] **Step 6: 提交**

```bash
git add backend/app/modules/providers backend/tests/test_model_router.py backend/tests/test_model_config.py
git commit -m "feat: add multi-model routing and encrypted config"
```

### Task 6: 六平台生成、质量检查、版本和审核流

**Files:**
- Create: `backend/app/modules/content/schemas.py`
- Create: `backend/app/modules/content/prompts.py`
- Create: `backend/app/modules/content/quality.py`
- Create: `backend/app/modules/content/service.py`
- Create: `backend/app/modules/content/routes.py`
- Test: `backend/tests/test_content_generation.py`
- Test: `backend/tests/test_review_workflow.py`

**Interfaces:**
- Produces: `POST /api/content-jobs`；`POST /api/content-jobs/{id}/analyze-images`；`POST /api/content-jobs/{id}/generate`；`POST /api/content-versions/{id}/generate-images`；`PATCH /api/content-versions/{id}`；`POST /api/content-jobs/{id}/submit`；`POST /api/content-jobs/{id}/review`。

- [ ] **Step 1: 写平台差异和状态机测试**

```python
def test_generated_job_is_waiting_for_review(client, operator_token, product_id):
    job = create_and_generate(client, operator_token, product_id, ["xiaohongshu", "wechat"])
    assert job["status"] == "pending_review"
    assert job["versions"][0]["body"] != job["versions"][1]["body"]
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_content_generation.py backend/tests/test_review_workflow.py -v`
Expected: FAIL，因为新工作流尚不存在。

- [ ] **Step 3: 定义结构化输出和平台字段**

```python
class PlatformContent(BaseModel):
    platform: Platform
    title: str
    body: str
    tags: list[str]
    keywords: list[str]
    optional_script: str | None = None
    cover_copy: str
    image_prompts: list[str]
```

- [ ] **Step 4: 实现质量规则与状态转换**

```python
ALLOWED_TRANSITIONS = {
    "draft": {"generating"},
    "generating": {"pending_review", "failed"},
    "pending_review": {"changes_requested", "approved"},
    "changes_requested": {"pending_review"},
}
```

图片分析中低置信度字段必须进入确认清单，生成配图写入素材表并关联内容版本：

```python
class ImageAnalysis(BaseModel):
    facts: dict[str, str]
    needs_confirmation: list[str]
    confidence: float = Field(ge=0, le=1)
```

- [ ] **Step 5: 运行内容与审核测试**

Run: `python -m pytest backend/tests/test_content_generation.py backend/tests/test_review_workflow.py -v`
Expected: PASS，运营不能自行审核，审核员不能修改模型密钥，低置信度图片结论不会直接写入正文。

- [ ] **Step 6: 提交**

```bash
git add backend/app/modules/content backend/tests/test_content_generation.py backend/tests/test_review_workflow.py
git commit -m "feat: add reviewed multi-platform content workflow"
```

### Task 7: 热点人工导入和模板结构库

**Files:**
- Create: `backend/app/modules/trends/schemas.py`
- Create: `backend/app/modules/trends/service.py`
- Create: `backend/app/modules/trends/routes.py`
- Test: `backend/tests/test_trends.py`

**Interfaces:**
- Produces: `POST /api/trends/import`；`GET /api/trends`；`POST /api/trends/{id}/archive`；`select_trend_context(platform, product_id)`。

- [ ] **Step 1: 写导入去重和来源记录测试**

```python
def test_duplicate_source_url_updates_existing_trend(client, admin_token):
    first = import_trend(client, admin_token, "https://example.com/a", "标题结构示例")
    second = import_trend(client, admin_token, "https://example.com/a", "更新后的内容")
    assert second["id"] == first["id"]
    assert second["source_url"] == "https://example.com/a"
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_trends.py -v`
Expected: FAIL，因为热点模块尚不存在。

- [ ] **Step 3: 实现人工导入、结构摘要和有效期**

```python
class TrendImport(BaseModel):
    platform: Platform
    source_url: HttpUrl | None = None
    source_text: str = Field(min_length=20, max_length=30000)
    expires_at: datetime | None = None
```

- [ ] **Step 4: 运行热点测试**

Run: `python -m pytest backend/tests/test_trends.py -v`
Expected: PASS，归档或过期热点不会进入生成上下文。

- [ ] **Step 5: 提交**

```bash
git add backend/app/modules/trends backend/tests/test_trends.py
git commit -m "feat: add sourced trend template library"
```

### Task 8: 发布适配器和人工发布包

**Files:**
- Create: `backend/app/modules/publishing/base.py`
- Create: `backend/app/modules/publishing/manual.py`
- Create: `backend/app/modules/publishing/service.py`
- Create: `backend/app/modules/publishing/routes.py`
- Test: `backend/tests/test_publishing.py`

**Interfaces:**
- Produces: `PlatformPublisher.publish(task) -> PublishResult`；`POST /api/content-jobs/{id}/publish-tasks`；`GET /api/publish-tasks`；`GET /api/publish-tasks/{id}/package`。

- [ ] **Step 1: 写无授权时人工包测试**

```python
def test_unconfigured_platform_creates_manual_package(client, reviewer_token, approved_job_id):
    response = client.post(f"/api/content-jobs/{approved_job_id}/publish-tasks", headers=auth(reviewer_token), json={"platform": "xiaohongshu"})
    assert response.status_code == 201
    assert response.json()["mode"] == "manual"
    assert response.json()["status"] == "ready_for_manual_publish"
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_publishing.py -v`
Expected: FAIL，因为发布模块尚不存在。

- [ ] **Step 3: 实现发布接口、人工包和有限重试字段**

```python
class PublishResult(BaseModel):
    status: Literal["published", "ready_for_manual_publish", "failed"]
    external_id: str | None = None
    error_code: str | None = None
```

- [ ] **Step 4: 运行发布测试**

Run: `python -m pytest backend/tests/test_publishing.py -v`
Expected: PASS，未授权平台不尝试模拟登录，失败最多重试 3 次。

- [ ] **Step 5: 提交**

```bash
git add backend/app/modules/publishing backend/tests/test_publishing.py
git commit -m "feat: add compliant publishing task adapters"
```

### Task 9: 效果数据与审计日志

**Files:**
- Create: `backend/app/modules/analytics/schemas.py`
- Create: `backend/app/modules/analytics/service.py`
- Create: `backend/app/modules/analytics/routes.py`
- Create: `backend/app/modules/audit/service.py`
- Test: `backend/tests/test_analytics.py`
- Test: `backend/tests/test_audit_log.py`

**Interfaces:**
- Produces: `POST /api/publish-tasks/{id}/metrics`；`GET /api/analytics/summary`；`record_audit(actor_id, action, entity_type, entity_id, details)`。

- [ ] **Step 1: 写效果录入和审计测试**

```python
def test_manual_metrics_are_attributed_to_publish_task(client, operator_token, published_task_id):
    response = client.post(f"/api/publish-tasks/{published_task_id}/metrics", headers=auth(operator_token), json={"views": 1200, "likes": 38, "favorites": 12, "inquiries": 3})
    assert response.status_code == 201
    assert response.json()["inquiries"] == 3
```

```python
def test_review_action_creates_audit_event(db, reviewed_job):
    event = db.scalar(select(AuditLog).where(AuditLog.entity_id == reviewed_job.id, AuditLog.action == "content.approved"))
    assert event is not None
```

- [ ] **Step 2: 运行并确认失败**

Run: `python -m pytest backend/tests/test_analytics.py backend/tests/test_audit_log.py -v`
Expected: FAIL，因为效果和审计服务尚不存在。

- [ ] **Step 3: 实现指标校验和统一审计入口**

```python
class ManualMetrics(BaseModel):
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    favorites: int = Field(default=0, ge=0)
    inquiries: int = Field(default=0, ge=0)
```

- [ ] **Step 4: 接入生成、修改、审核、发布和设置变更日志**

```python
record_audit(db, current_user.id, "content.approved", "content_job", job.id, {"comment": request.comment})
```

- [ ] **Step 5: 运行测试**

Run: `python -m pytest backend/tests/test_analytics.py backend/tests/test_audit_log.py -v`
Expected: PASS，负数指标返回 422，密钥内容不进入审计详情。

- [ ] **Step 6: 提交**

```bash
git add backend/app/modules/analytics backend/app/modules/audit backend/tests/test_analytics.py backend/tests/test_audit_log.py
git commit -m "feat: add performance metrics and audit logs"
```

### Task 10: 前端登录、后台布局和 API 客户端

**Files:**
- Create: `frontend/src/features/auth/AuthProvider.tsx`
- Create: `frontend/src/features/auth/LoginPage.tsx`
- Create: `frontend/src/layout/AppShell.tsx`
- Create: `frontend/src/lib/apiClient.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/features/auth/LoginPage.test.tsx`
- Test: `frontend/src/layout/AppShell.test.tsx`

**Interfaces:**
- Consumes: `/api/auth/login`, `/api/auth/me`。
- Produces: `useAuth()`；统一带 Bearer token 的 `apiClient`；专业后台式响应布局。

- [ ] **Step 1: 写登录和角色导航测试**

```tsx
expect(screen.getByRole("heading", { name: "明景内容运营助手" })).toBeInTheDocument();
await user.type(screen.getByLabelText("账号"), "admin");
await user.type(screen.getByLabelText("密码"), "StrongPass123!");
await user.click(screen.getByRole("button", { name: "登录" }));
expect(await screen.findByText("内容创作")).toBeInTheDocument();
```

- [ ] **Step 2: 运行并确认失败**

Run: `pnpm --dir frontend test -- LoginPage.test.tsx AppShell.test.tsx`
Expected: FAIL，因为登录页面和后台壳不存在。

- [ ] **Step 3: 实现登录态、401 清理和左侧导航**

```ts
export async function apiClient<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("mingjing_access_token");
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers: { ...init.headers, ...(token ? { Authorization: `Bearer ${token}` } : {}) } });
  if (response.status === 401) localStorage.removeItem("mingjing_access_token");
  if (!response.ok) throw new Error(await readApiError(response));
  return response.json() as Promise<T>;
}
```

- [ ] **Step 4: 运行前端测试和构建**

Run: `pnpm --dir frontend test && pnpm --dir frontend build`
Expected: PASS，360px 宽度下导航可收起且按钮文字不溢出。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/features/auth frontend/src/layout frontend/src/lib frontend/src/App.tsx frontend/src/styles.css
git commit -m "feat: add authenticated operations shell"
```

### Task 11: 前端产品、创作、审核和发布页面

**Files:**
- Create: `frontend/src/features/catalog/ProductLibraryPage.tsx`
- Create: `frontend/src/features/creation/CreationPage.tsx`
- Create: `frontend/src/features/creation/PlatformResultEditor.tsx`
- Create: `frontend/src/features/review/ReviewQueuePage.tsx`
- Create: `frontend/src/features/publishing/PublishTasksPage.tsx`
- Create: `frontend/src/features/trends/TrendLibraryPage.tsx`
- Create: `frontend/src/features/analytics/AnalyticsPage.tsx`
- Modify: `frontend/src/types.ts`
- Test: `frontend/src/features/creation/CreationPage.test.tsx`
- Test: `frontend/src/features/review/ReviewQueuePage.test.tsx`

**Interfaces:**
- Consumes: Tasks 4, 6, 7, 8 的 REST API。
- Produces: 图片与需求创建流程、六平台标签页编辑、生成配图、审核队列、人工发布包下载和人工效果录入。

- [ ] **Step 1: 写完整用户流程测试**

```tsx
await user.upload(screen.getByLabelText("上传产品图片"), productImage);
await user.type(screen.getByLabelText("推广需求"), "面向箱包采购，强调来样定制");
await user.click(screen.getByRole("button", { name: "生成六平台内容" }));
expect(await screen.findByRole("tab", { name: "小红书" })).toBeInTheDocument();
expect(screen.getByRole("button", { name: "生成配图" })).toBeEnabled();
expect(screen.getByRole("button", { name: "提交审核" })).toBeEnabled();
```

- [ ] **Step 2: 运行并确认失败**

Run: `pnpm --dir frontend test -- CreationPage.test.tsx ReviewQueuePage.test.tsx`
Expected: FAIL，因为新页面尚不存在。

- [ ] **Step 3: 实现创建表单和稳定布局**

```tsx
<div className="platform-tabs" role="tablist">
  {versions.map((version) => <button role="tab" key={version.platform}>{PLATFORM_LABELS[version.platform]}</button>)}
</div>
```

- [ ] **Step 4: 实现审核队列和发布任务页**

```tsx
<button aria-label="通过内容" onClick={() => review(job.id, "approved")}>通过</button>
<button aria-label="退回修改" onClick={() => review(job.id, "changes_requested")}>退回</button>
```

- [ ] **Step 5: 运行所有前端测试和构建**

Run: `pnpm --dir frontend test && pnpm --dir frontend build`
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/features frontend/src/types.ts
git commit -m "feat: add end-to-end content operations workflow"
```

### Task 12: 云端容器、端到端验收和文档

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `deploy/docker-compose.yml`
- Create: `deploy/nginx.conf`
- Create: `.env.example`
- Create: `docs/deployment.md`
- Create: `backend/tests/test_phase_one_acceptance.py`
- Modify: `README.md`

**Interfaces:**
- Produces: `docker compose -f deploy/docker-compose.yml up --build`；前端 `/`；后端 `/api`；PostgreSQL 持久卷；上传目录持久卷。

- [ ] **Step 1: 写后端闭环验收测试**

```python
def test_phase_one_content_lifecycle(client, admin_token, reviewer_token, stub_model):
    product = create_product(client, admin_token)
    job = create_generate_and_submit(client, admin_token, product["id"])
    approved = review_job(client, reviewer_token, job["id"], "approved")
    task = create_publish_task(client, reviewer_token, approved["id"], "xiaohongshu")
    assert task["status"] == "ready_for_manual_publish"
```

- [ ] **Step 2: 运行验收测试并确认缺少部署配置**

Run: `python -m pytest backend/tests/test_phase_one_acceptance.py -v`
Expected: PASS 后再进入容器步骤；若失败，修复对应业务任务，不在部署层绕过。

- [ ] **Step 3: 编写容器和环境变量**

```yaml
services:
  db:
    image: postgres:17-alpine
  api:
    build: ../backend
    depends_on: [db]
  web:
    build: ../frontend
    depends_on: [api]
```

- [ ] **Step 4: 运行全量验证**

Run: `python -m pytest backend/tests -q`
Expected: PASS。

Run: `pnpm --dir frontend test && pnpm --dir frontend build`
Expected: PASS。

Run: `docker compose -f deploy/docker-compose.yml config`
Expected: 配置解析成功且无缺失变量。

- [ ] **Step 5: 启动并做浏览器验收**

Run: `docker compose -f deploy/docker-compose.yml up --build -d`
Expected: `GET http://127.0.0.1/health` 返回 200；登录、上传、生成、审核和人工发布包流程可完成。

- [ ] **Step 6: 更新使用与部署文档**

```markdown
1. 从 `.env.example` 创建服务器环境配置。
2. 设置强随机 `JWT_SECRET` 和 `CONFIG_ENCRYPTION_KEY`。
3. 运行数据库迁移并创建首个管理员。
4. 在设置页填写模型密钥；平台密钥可后续补充。
```

- [ ] **Step 7: 提交**

```bash
git add backend/Dockerfile frontend/Dockerfile deploy .env.example docs/deployment.md README.md backend/tests/test_phase_one_acceptance.py
git commit -m "feat: package mingjing phase one for cloud deployment"
```

## 后续独立计划

- 方案 C 自动视频生成。
- 合规公开热点自动采集调度器。
- 六个平台真实 OAuth、发布和数据回收适配器。
- 搜索关联监测、客户线索和智能选题分析。
