# Mingjing Content Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first cloud-ready version of the Mingjing content operations platform, covering product assets, six-platform AI content generation, trend templates, image assets, and one unified manual/automatic publishing center.

**Architecture:** A React and TypeScript admin frontend consumes a modular FastAPI API. PostgreSQL stores business data, an object-storage interface owns files, and background jobs call replaceable model, trend, image, and publishing adapters. The first release enables one administrator while keeping organization, role, and adapter boundaries ready for later expansion.

**Tech Stack:** React 19, TypeScript 5, Vite 7, TanStack Query, React Router, Vitest, Testing Library, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, PostgreSQL 16, Redis 7, Dramatiq, pytest, Playwright, Docker Compose.

## Global Constraints

- The brand name in all visible copy is exactly `明景`; never use `明璟`.
- The product must work in current desktop and mobile Chromium browsers.
- The first release enables one administrator account but persists organization, user, role, and resource ownership fields.
- Doubao is the default content model; DeepSeek, Qwen, and OpenAI are configurable fallbacks.
- Automatic publishing uses official platform APIs only and requires a final human confirmation.
- Platforms without official authorization fall back to the complete manual publishing flow.
- Never store platform passwords, bypass verification codes, or simulate clicks to evade platform restrictions.
- Trend sources retain provenance and only contribute structural patterns; source text is not copied.
- Uploaded originals are retained and AI image-analysis results remain editable.
- The system improves truthful public content association and never promises or manipulates search ranking.
- Scheme C capabilities are extension interfaces only in phase one: video generation, expanded collectors, search association monitoring, lead capture, and advanced analytics.

---

## Planned File Structure

```text
mingjing-content-platform/
  compose.yaml                    # local PostgreSQL, Redis, API, worker, web
  .env.example                    # documented non-secret configuration
  backend/
    pyproject.toml                # Python dependencies and test configuration
    alembic.ini
    migrations/                   # schema migrations
    app/
      main.py                     # FastAPI application assembly
      core/                       # settings, security, errors, logging
      db/                         # engine, sessions, declarative base
      auth/                       # administrator login and future role model
      catalog/                    # company and product records
      storage/                    # object-storage contract and local adapter
      providers/                  # AI text and image provider contracts
      content/                    # projects, platform variants, generation jobs
      trends/                     # provenance and structural template extraction
      publishing/                 # manual and official API publishing workflows
      analytics/                  # operational metrics
      audit/                      # immutable audit events
      extensions/                 # Scheme C extension registry
      worker.py                   # background-job registration
    tests/                        # backend unit and integration tests
  frontend/
    package.json
    src/
      app/                        # router, query client, authenticated shell
      api/                        # typed API client
      features/auth/
      features/creation/
      features/catalog/
      features/content-library/
      features/trends/
      features/publishing/
      features/settings/
      features/analytics/
      components/                 # shared controls only
      styles/                     # tokens and global responsive layout
    tests/
    e2e/
  docs/
    operations.md                 # setup, backup, restore, provider configuration
```

## Task 1: Repository Foundation and Health Contract

**Files:**
- Create: `mingjing-content-platform/backend/pyproject.toml`
- Create: `mingjing-content-platform/backend/app/main.py`
- Create: `mingjing-content-platform/backend/app/core/settings.py`
- Create: `mingjing-content-platform/backend/tests/test_health.py`
- Create: `mingjing-content-platform/frontend/package.json`
- Create: `mingjing-content-platform/frontend/src/main.tsx`
- Create: `mingjing-content-platform/frontend/src/app/App.tsx`
- Create: `mingjing-content-platform/frontend/src/app/App.test.tsx`
- Create: `mingjing-content-platform/compose.yaml`
- Create: `mingjing-content-platform/.env.example`

**Interfaces:**
- Produces: `GET /api/health -> {"status":"ok","service":"mingjing-api"}`.
- Produces: frontend application root with the visible brand `明景`.

- [ ] **Step 1: Write failing backend and frontend smoke tests**

```python
def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "mingjing-api"}
```

```tsx
it("renders the Mingjing brand", () => {
  render(<App />)
  expect(screen.getByText("明景")).toBeInTheDocument()
})
```

- [ ] **Step 2: Run the smoke tests and confirm both fail**

Run: `cd mingjing-content-platform/backend; pytest tests/test_health.py -q`  
Expected: FAIL because `app.main` does not exist.

Run: `cd mingjing-content-platform/frontend; pnpm vitest run src/app/App.test.tsx`  
Expected: FAIL because `App` does not exist.

- [ ] **Step 3: Implement the minimal health API and application root**

```python
from fastapi import FastAPI

app = FastAPI(title="Mingjing Content Platform")

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mingjing-api"}
```

```tsx
export function App() {
  return <main><h1>明景</h1></main>
}
```

- [ ] **Step 4: Add pinned dependencies, environment validation, and Compose services**

Configure PostgreSQL 16, Redis 7, API, worker, and frontend services. `.env.example` must contain non-secret names for `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `STORAGE_ROOT`, and provider keys with empty values.

- [ ] **Step 5: Run all smoke checks**

Run: `cd mingjing-content-platform/backend; pytest -q`  
Expected: PASS.

Run: `cd mingjing-content-platform/frontend; pnpm test -- --run`  
Expected: PASS.

Run: `docker compose -f mingjing-content-platform/compose.yaml config`  
Expected: valid merged configuration with no interpolation errors.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform
git commit -m "build: scaffold Mingjing platform services"
```

## Task 2: Database, Authentication, and Audit Foundation

**Files:**
- Create: `mingjing-content-platform/backend/app/db/base.py`
- Create: `mingjing-content-platform/backend/app/db/session.py`
- Create: `mingjing-content-platform/backend/app/auth/models.py`
- Create: `mingjing-content-platform/backend/app/auth/schemas.py`
- Create: `mingjing-content-platform/backend/app/auth/service.py`
- Create: `mingjing-content-platform/backend/app/auth/routes.py`
- Create: `mingjing-content-platform/backend/app/audit/models.py`
- Create: `mingjing-content-platform/backend/app/audit/service.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0001_auth_audit.py`
- Create: `mingjing-content-platform/backend/tests/auth/test_login.py`
- Create: `mingjing-content-platform/backend/tests/audit/test_audit_events.py`

**Interfaces:**
- Produces: `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.
- Produces: `record_audit(session, actor_id, action, resource_type, resource_id, metadata)`.
- Produces: tables `organizations`, `users`, `roles`, `user_roles`, `sessions`, `audit_events`.

- [ ] **Step 1: Write failing login and audit tests**

```python
def test_admin_can_login(client, seeded_admin):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "correct-password"})
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "administrator"
    assert response.cookies.get("mingjing_session")

def test_wrong_password_is_rejected(client, seeded_admin):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"
```

- [ ] **Step 2: Run the focused tests**

Run: `cd mingjing-content-platform/backend; pytest tests/auth tests/audit -q`  
Expected: FAIL because authentication models and routes are absent.

- [ ] **Step 3: Implement password hashing, revocable sessions, and organization ownership**

Use Argon2 password hashes. Set the session token in an `HttpOnly`, `SameSite=Lax` cookie; store only its SHA-256 digest. Seed exactly one administrator from environment variables on the first deployment.

```python
def require_admin(user: User = Depends(current_user)) -> User:
    if "administrator" not in user.role_names:
        raise ApiError(403, "administrator_required", "需要管理员权限")
    return user
```

- [ ] **Step 4: Add immutable audit writes to login, logout, and configuration changes**

Audit metadata must be JSON-safe and must exclude passwords, raw session tokens, API keys, and platform tokens.

- [ ] **Step 5: Run migration and tests**

Run: `cd mingjing-content-platform/backend; alembic upgrade head`  
Expected: migration completes and creates six auth/audit tables.

Run: `cd mingjing-content-platform/backend; pytest tests/auth tests/audit -q`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add administrator authentication and audit log"
```

## Task 3: Product Catalog and Object Storage

**Files:**
- Create: `mingjing-content-platform/backend/app/catalog/models.py`
- Create: `mingjing-content-platform/backend/app/catalog/schemas.py`
- Create: `mingjing-content-platform/backend/app/catalog/service.py`
- Create: `mingjing-content-platform/backend/app/catalog/routes.py`
- Create: `mingjing-content-platform/backend/app/storage/base.py`
- Create: `mingjing-content-platform/backend/app/storage/local.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0002_catalog_assets.py`
- Create: `mingjing-content-platform/backend/tests/catalog/test_products.py`
- Create: `mingjing-content-platform/backend/tests/storage/test_local_storage.py`

**Interfaces:**
- Produces: CRUD endpoints under `/api/products` and upload endpoint `/api/assets`.
- Produces: `Storage.put(stream, content_type) -> StoredObject` and `Storage.open(key) -> BinaryIO`.
- Produces: tables `company_profiles`, `products`, `assets`, `product_assets`.

- [ ] **Step 1: Write failing catalog and upload tests**

```python
def test_create_product_with_factory_fields(auth_client):
    response = auth_client.post("/api/products", json={
        "name": "环保棉绳", "material": "再生棉", "specification": "5mm",
        "colors": ["本白"], "uses": ["礼品包装"], "advantages": ["支持定制"]
    })
    assert response.status_code == 201
    assert response.json()["name"] == "环保棉绳"
```

- [ ] **Step 2: Verify focused tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/catalog tests/storage -q`  
Expected: FAIL because catalog and storage modules do not exist.

- [ ] **Step 3: Implement focused models, services, and local storage traversal protection**

Reject unsupported MIME types, files over the configured size, empty files, and any storage key that resolves outside `STORAGE_ROOT`. Calculate SHA-256 for deduplication while always retaining the original logical asset record.

- [ ] **Step 4: Run migration and focused tests**

Run: `cd mingjing-content-platform/backend; alembic upgrade head; pytest tests/catalog tests/storage -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add product catalog and asset storage"
```

## Task 4: Provider Router and Editable Image Understanding

**Files:**
- Create: `mingjing-content-platform/backend/app/providers/contracts.py`
- Create: `mingjing-content-platform/backend/app/providers/router.py`
- Create: `mingjing-content-platform/backend/app/providers/config_crypto.py`
- Create: `mingjing-content-platform/backend/app/providers/doubao.py`
- Create: `mingjing-content-platform/backend/app/providers/openai_compatible.py`
- Create: `mingjing-content-platform/backend/app/providers/routes.py`
- Create: `mingjing-content-platform/backend/tests/providers/test_router.py`
- Create: `mingjing-content-platform/backend/tests/providers/test_image_analysis.py`

**Interfaces:**
- Consumes: authenticated administrator and stored assets.
- Produces: `TextProvider.generate(request: GenerationRequest) -> GenerationResponse`.
- Produces: `VisionProvider.analyze(asset: Asset) -> ProductObservation`.
- Produces: `ProviderRouter.run(capability, request) -> ProviderResult` with ordered fallback.

- [ ] **Step 1: Write failing fallback and observation tests**

```python
def test_router_falls_back_after_retryable_failure():
    primary = StubProvider(error=RetryableProviderError("timeout"))
    fallback = StubProvider(result={"title": "棉绳采购指南"})
    result = ProviderRouter([primary, fallback]).run("text", request={})
    assert result.provider_name == fallback.name

def test_observation_is_not_applied_until_confirmed(auth_client, uploaded_asset):
    response = auth_client.post(f"/api/assets/{uploaded_asset.id}/analyze")
    assert response.json()["status"] == "needs_confirmation"
```

- [ ] **Step 2: Confirm tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/providers -q`  
Expected: FAIL because provider contracts do not exist.

- [ ] **Step 3: Implement provider contracts, encrypted configuration, timeout handling, and fallback policy**

The default text route order is `doubao`, `deepseek`, `qwen`, `openai`. Authentication and quota errors are surfaced without retrying the same provider; timeouts and service errors allow the next configured provider.

- [ ] **Step 4: Implement image-analysis confirmation records**

Persist detected category, material, colors, texture, scenes, provider, and raw confidence separately from user-confirmed values. Content generation reads confirmed values only.

- [ ] **Step 5: Run provider tests**

Run: `cd mingjing-content-platform/backend; pytest tests/providers -q`  
Expected: PASS with fallback, non-retryable error, redaction, and confirmation cases covered.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add configurable AI providers and image analysis"
```

## Task 5: Content Projects and Six-Platform Generation

**Files:**
- Create: `mingjing-content-platform/backend/app/content/models.py`
- Create: `mingjing-content-platform/backend/app/content/schemas.py`
- Create: `mingjing-content-platform/backend/app/content/platform_rules.py`
- Create: `mingjing-content-platform/backend/app/content/prompts.py`
- Create: `mingjing-content-platform/backend/app/content/service.py`
- Create: `mingjing-content-platform/backend/app/content/routes.py`
- Create: `mingjing-content-platform/backend/app/content/jobs.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0003_content.py`
- Create: `mingjing-content-platform/backend/tests/content/test_generation.py`
- Create: `mingjing-content-platform/backend/tests/content/test_versions.py`

**Interfaces:**
- Consumes: confirmed product observations, product records, provider router, and optional trend structure.
- Produces: `POST /api/content-projects`, `POST /api/content-projects/{id}/generate`, and variant edit/version endpoints.
- Produces: six `PlatformVariant` records keyed by `xiaohongshu`, `douyin`, `kuaishou`, `toutiao`, `channels`, `wechat_official`.

- [ ] **Step 1: Write a failing contract test for all six outputs**

```python
def test_generation_creates_six_platform_variants(auth_client, product):
    project = auth_client.post("/api/content-projects", json={
        "product_id": str(product.id), "requirements": "面向礼品包装采购商",
        "platforms": ["xiaohongshu", "douyin", "kuaishou", "toutiao", "channels", "wechat_official"]
    }).json()
    response = auth_client.post(f"/api/content-projects/{project['id']}/generate")
    assert response.status_code == 202
    assert set(response.json()["platforms"]) == {
        "xiaohongshu", "douyin", "kuaishou", "toutiao", "channels", "wechat_official"
    }
```

- [ ] **Step 2: Verify content tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/content -q`  
Expected: FAIL because content project APIs are absent.

- [ ] **Step 3: Implement platform-specific typed output schemas**

Each variant stores title, body, tags, keywords, cover copy, image guidance, optional spoken script, optional shot list, model, template, prompt version, and edit version. Validate required fields per platform before marking a job successful.

- [ ] **Step 4: Implement idempotent background generation and version editing**

`POST generate` returns an existing running job for the same project revision and platform set. Editing creates a new immutable revision while updating the current revision pointer.

- [ ] **Step 5: Run migrations and tests**

Run: `cd mingjing-content-platform/backend; alembic upgrade head; pytest tests/content -q`  
Expected: PASS for all platforms, retries, validation failure, idempotency, and versions.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: generate versioned content for six platforms"
```

## Task 6: Trend Template Provenance and Structural Extraction

**Files:**
- Create: `mingjing-content-platform/backend/app/trends/models.py`
- Create: `mingjing-content-platform/backend/app/trends/contracts.py`
- Create: `mingjing-content-platform/backend/app/trends/extractor.py`
- Create: `mingjing-content-platform/backend/app/trends/manual.py`
- Create: `mingjing-content-platform/backend/app/trends/routes.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0004_trends.py`
- Create: `mingjing-content-platform/backend/tests/trends/test_manual_import.py`
- Create: `mingjing-content-platform/backend/tests/trends/test_extraction_boundaries.py`

**Interfaces:**
- Produces: `POST /api/trend-sources/import` and template listing/filter endpoints.
- Produces: `TrendCollector.collect() -> list[TrendCandidate]` extension contract.
- Produces: structural fields `headline_pattern`, `opening_hook`, `section_rhythm`, `content_angle`, `interaction_pattern`.

- [ ] **Step 1: Write failing provenance and no-copy tests**

```python
def test_manual_import_keeps_provenance_and_excludes_source_body(auth_client):
    response = auth_client.post("/api/trend-sources/import", json={
        "url": "https://example.com/source", "title": "采购棉绳先看这三点",
        "body": "一段仅用于分析结构的来源正文"
    })
    payload = response.json()
    assert payload["source_url"] == "https://example.com/source"
    assert "一段仅用于分析" not in payload["template"]["reusable_text"]
```

- [ ] **Step 2: Verify trend tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/trends -q`  
Expected: FAIL because trend models and extractor are absent.

- [ ] **Step 3: Implement manual import, provenance, deduplication, and structural extraction**

Store a hash and source metadata, but do not expose source body as reusable template text. Reject URLs requiring authentication or using schemes other than HTTPS/HTTP.

- [ ] **Step 4: Run migration and tests**

Run: `cd mingjing-content-platform/backend; alembic upgrade head; pytest tests/trends -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add sourced trend structure library"
```

## Task 7: Generated Image Assets

**Files:**
- Create: `mingjing-content-platform/backend/app/providers/image_contracts.py`
- Create: `mingjing-content-platform/backend/app/content/image_service.py`
- Create: `mingjing-content-platform/backend/app/content/image_routes.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0005_generated_assets.py`
- Create: `mingjing-content-platform/backend/tests/content/test_image_generation.py`

**Interfaces:**
- Consumes: original assets, confirmed product data, content variant, and image provider.
- Produces: `POST /api/content-projects/{id}/images` and generated asset metadata.
- Produces: `ImageProvider.generate(request: ImageGenerationRequest) -> GeneratedImage`.

- [ ] **Step 1: Write failing image provenance tests**

```python
def test_generated_image_retains_original_and_generation_metadata(auth_client, project, asset):
    response = auth_client.post(f"/api/content-projects/{project.id}/images", json={
        "source_asset_ids": [str(asset.id)], "kind": "cover", "count": 1
    })
    assert response.status_code == 202
    job = wait_for_job(response.json()["job_id"])
    assert job["assets"][0]["source_asset_ids"] == [str(asset.id)]
    assert job["assets"][0]["prompt_version"]
```

- [ ] **Step 2: Confirm tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/content/test_image_generation.py -q`  
Expected: FAIL because image generation endpoints are absent.

- [ ] **Step 3: Implement image job, provenance, dimensions, and rejection state**

Support `cover`, `product_poster`, and `article_support`. Store prompt, provider, model, dimensions, source assets, and user acceptance state. Never delete or overwrite original assets.

- [ ] **Step 4: Run focused and content regression tests**

Run: `cd mingjing-content-platform/backend; pytest tests/content -q`  
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add traceable AI image assets"
```

## Task 8: Unified Manual and Automatic Publishing Domain

**Files:**
- Create: `mingjing-content-platform/backend/app/publishing/models.py`
- Create: `mingjing-content-platform/backend/app/publishing/contracts.py`
- Create: `mingjing-content-platform/backend/app/publishing/manual.py`
- Create: `mingjing-content-platform/backend/app/publishing/mock_official.py`
- Create: `mingjing-content-platform/backend/app/publishing/service.py`
- Create: `mingjing-content-platform/backend/app/publishing/routes.py`
- Create: `mingjing-content-platform/backend/app/publishing/jobs.py`
- Create: `mingjing-content-platform/backend/migrations/versions/0006_publishing.py`
- Create: `mingjing-content-platform/backend/tests/publishing/test_manual_flow.py`
- Create: `mingjing-content-platform/backend/tests/publishing/test_automatic_flow.py`

**Interfaces:**
- Consumes: approved content variants, assets, administrator confirmation, and platform adapter capability.
- Produces: publication tasks with states `pending`, `running`, `needs_confirmation`, `succeeded`, `failed`, `cancelled`.
- Produces: `Publisher.capabilities(account)`, `publish(request)`, `status(remote_id)`, `cancel(remote_id)`.

- [ ] **Step 1: Write failing manual fallback and idempotency tests**

```python
def test_unauthorized_automatic_platform_falls_back_to_manual(auth_client, approved_variant):
    response = auth_client.post("/api/publications", json={
        "variant_id": str(approved_variant.id), "mode": "automatic", "confirmed": True
    })
    assert response.status_code == 201
    assert response.json()["effective_mode"] == "manual"
    assert response.json()["reason"] == "official_authorization_required"

def test_duplicate_confirmation_does_not_duplicate_remote_publish(auth_client, automatic_task):
    first = auth_client.post(f"/api/publications/{automatic_task.id}/confirm")
    second = auth_client.post(f"/api/publications/{automatic_task.id}/confirm")
    assert first.json()["job_id"] == second.json()["job_id"]
```

- [ ] **Step 2: Verify publishing tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/publishing -q`  
Expected: FAIL because publishing domain is absent.

- [ ] **Step 3: Implement manual package preparation and official adapter capability checks**

Manual packages contain title, body, tags, script, downloadable assets, official publishing URL, and fields for recording published time and URL. Automatic tasks require `confirmed=True` and an authorized adapter capability.

- [ ] **Step 4: Implement scheduling, cancellation, retry, idempotency, and audit events**

Every external publish call uses a stable idempotency key derived from publication task ID and revision. Failed automatic tasks expose a manual conversion action without losing content.

- [ ] **Step 5: Run migrations and publishing tests**

Run: `cd mingjing-content-platform/backend; alembic upgrade head; pytest tests/publishing -q`  
Expected: PASS for manual, automatic mock, failure, retry, cancel, and duplicate confirmation.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/backend
git commit -m "feat: add unified manual and automatic publishing"
```

## Task 9: Authenticated Admin Shell and Responsive Creation Workspace

**Files:**
- Create: `mingjing-content-platform/frontend/src/api/client.ts`
- Create: `mingjing-content-platform/frontend/src/features/auth/LoginPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/auth/AuthProvider.tsx`
- Create: `mingjing-content-platform/frontend/src/app/AppShell.tsx`
- Create: `mingjing-content-platform/frontend/src/features/creation/CreationPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/creation/CreationForm.tsx`
- Create: `mingjing-content-platform/frontend/src/features/creation/AdvancedSettings.tsx`
- Create: `mingjing-content-platform/frontend/src/features/creation/PlatformPreview.tsx`
- Create: `mingjing-content-platform/frontend/src/styles/tokens.css`
- Create: `mingjing-content-platform/frontend/src/styles/layout.css`
- Create: `mingjing-content-platform/frontend/src/features/creation/CreationPage.test.tsx`
- Create: `mingjing-content-platform/frontend/src/app/AppShell.test.tsx`

**Interfaces:**
- Consumes: auth, products, assets, content project, job, and variant APIs.
- Produces: confirmed left-navigation shell and default creation route `/create`.

- [ ] **Step 1: Write failing shell and creation workflow tests**

```tsx
it("opens content creation as the authenticated default", async () => {
  renderApp({ route: "/" })
  expect(await screen.findByRole("heading", { name: "内容创作" })).toBeVisible()
  expect(screen.getByRole("navigation")).toHaveTextContent("发布中心")
})

it("keeps advanced settings collapsed by default", async () => {
  renderApp({ route: "/create" })
  expect(await screen.findByRole("button", { name: "高级设置" })).toHaveAttribute("aria-expanded", "false")
})
```

- [ ] **Step 2: Verify frontend tests fail**

Run: `cd mingjing-content-platform/frontend; pnpm vitest run`  
Expected: FAIL because authenticated shell and creation components are absent.

- [ ] **Step 3: Implement the enterprise shell and creation form**

Use a restrained neutral palette with green as the action color, 8px-or-less radii, Lucide icons, stable control dimensions, and no nested cards. Desktop uses a 190px sidebar; mobile uses a drawer and stacks form above preview.

- [ ] **Step 4: Implement upload, autosave, generation progress, editable previews, and per-platform retry**

Autosave local edits after 800ms idle and reconcile with the latest server revision. Show platform-specific errors without clearing successful variants.

- [ ] **Step 5: Run component tests and type checking**

Run: `cd mingjing-content-platform/frontend; pnpm vitest run; pnpm tsc --noEmit`  
Expected: PASS with no TypeScript errors.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/frontend
git commit -m "feat: add responsive content creation workspace"
```

## Task 10: Catalog, Trend, Library, Settings, and Analytics Screens

**Files:**
- Create: `mingjing-content-platform/frontend/src/features/catalog/CatalogPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/trends/TrendLibraryPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/content-library/ContentLibraryPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/settings/SettingsPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/analytics/AnalyticsPage.tsx`
- Create: `mingjing-content-platform/backend/app/analytics/service.py`
- Create: `mingjing-content-platform/backend/app/analytics/routes.py`
- Create: `mingjing-content-platform/frontend/src/features/catalog/CatalogPage.test.tsx`
- Create: `mingjing-content-platform/frontend/src/features/trends/TrendLibraryPage.test.tsx`
- Create: `mingjing-content-platform/backend/tests/analytics/test_metrics.py`

**Interfaces:**
- Consumes: APIs built in Tasks 2-8.
- Produces: operational screens linked from the left navigation.
- Produces: `GET /api/analytics/summary` with content count, publish count, success rate, and failure count.

- [ ] **Step 1: Write failing screen and metrics tests**

```python
def test_summary_counts_publication_outcomes(auth_client, seeded_publications):
    payload = auth_client.get("/api/analytics/summary").json()
    assert payload["publication_count"] == 3
    assert payload["publication_success_rate"] == 2 / 3
```

- [ ] **Step 2: Verify focused tests fail**

Run: `cd mingjing-content-platform/backend; pytest tests/analytics -q`  
Expected: FAIL because analytics service is absent.

Run: `cd mingjing-content-platform/frontend; pnpm vitest run src/features/catalog src/features/trends`  
Expected: FAIL because feature pages are absent.

- [ ] **Step 3: Implement operational screens with search, filtering, pagination, loading, empty, and error states**

Provider keys must render only configured/not-configured state and last four identifying characters; no endpoint returns full secret values.

- [ ] **Step 4: Implement aggregate metrics from local operational records**

Phase-one analytics use content and publication records only. Do not invent platform performance metrics that have not been imported or authorized.

- [ ] **Step 5: Run focused and regression tests**

Run: `cd mingjing-content-platform/backend; pytest -q`  
Expected: PASS.

Run: `cd mingjing-content-platform/frontend; pnpm vitest run; pnpm tsc --noEmit`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform
git commit -m "feat: add operational management screens"
```

## Task 11: Unified Publishing Center Frontend

**Files:**
- Create: `mingjing-content-platform/frontend/src/features/publishing/PublishingPage.tsx`
- Create: `mingjing-content-platform/frontend/src/features/publishing/ManualPublishPanel.tsx`
- Create: `mingjing-content-platform/frontend/src/features/publishing/AutomaticPublishPanel.tsx`
- Create: `mingjing-content-platform/frontend/src/features/publishing/PublicationStatus.tsx`
- Create: `mingjing-content-platform/frontend/src/features/publishing/PublishingPage.test.tsx`

**Interfaces:**
- Consumes: publication creation, confirmation, status, retry, cancel, manual conversion, and capability APIs.
- Produces: one page where manual and automatic publishing are visible together.

- [ ] **Step 1: Write failing publishing-center interaction tests**

```tsx
it("shows manual and automatic publishing together", async () => {
  renderApp({ route: "/publishing" })
  expect(await screen.findByRole("heading", { name: "人工发布" })).toBeVisible()
  expect(screen.getByRole("heading", { name: "自动发布" })).toBeVisible()
})

it("explains official authorization fallback", async () => {
  renderApp({ route: "/publishing", capabilities: { xiaohongshu: false } })
  expect(await screen.findByText("需要平台官方接口授权")).toBeVisible()
  expect(screen.getByRole("button", { name: "转为人工发布" })).toBeEnabled()
})
```

- [ ] **Step 2: Verify the focused tests fail**

Run: `cd mingjing-content-platform/frontend; pnpm vitest run src/features/publishing`  
Expected: FAIL because publishing components are absent.

- [ ] **Step 3: Implement side-by-side workflows and final confirmation dialog**

The confirmation shows platform account, title, body summary, asset count, schedule, and effective mode. Disable automatic confirmation when capability is unavailable and keep manual conversion available.

- [ ] **Step 4: Implement polling, retry, cancellation, copy, download, official-entry link, and published-link recording**

Use stable status dimensions so progress labels do not shift the layout. Surface platform error codes with a concise Chinese explanation.

- [ ] **Step 5: Run frontend regression tests**

Run: `cd mingjing-content-platform/frontend; pnpm vitest run; pnpm tsc --noEmit`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add mingjing-content-platform/frontend
git commit -m "feat: add unified publishing center interface"
```

## Task 12: Scheme C Extension Registry

**Files:**
- Create: `mingjing-content-platform/backend/app/extensions/contracts.py`
- Create: `mingjing-content-platform/backend/app/extensions/registry.py`
- Create: `mingjing-content-platform/backend/app/extensions/routes.py`
- Create: `mingjing-content-platform/backend/tests/extensions/test_registry.py`

**Interfaces:**
- Produces: extension identifiers `video_generation`, `trend_collectors`, `search_association`, `lead_capture`, `advanced_analytics`.
- Produces: read-only `GET /api/extensions` capability response.

- [ ] **Step 1: Write a failing registry test**

```python
def test_phase_one_extensions_are_declared_but_disabled(auth_client):
    payload = auth_client.get("/api/extensions").json()
    assert {item["id"] for item in payload} == {
        "video_generation", "trend_collectors", "search_association", "lead_capture", "advanced_analytics"
    }
    assert all(item["enabled"] is False for item in payload)
```

- [ ] **Step 2: Verify the test fails**

Run: `cd mingjing-content-platform/backend; pytest tests/extensions -q`  
Expected: FAIL because the extension registry is absent.

- [ ] **Step 3: Implement a typed registry without placeholder business logic**

The registry declares ID, display name, required capability, enabled state, and future route namespace. It does not create empty services or database tables before a Scheme C feature is approved.

- [ ] **Step 4: Run tests and commit**

Run: `cd mingjing-content-platform/backend; pytest tests/extensions -q`  
Expected: PASS.

```bash
git add mingjing-content-platform/backend
git commit -m "feat: reserve Scheme C extension registry"
```

## Task 13: End-to-End Verification, Operations, and Cloud-Ready Packaging

**Files:**
- Create: `mingjing-content-platform/frontend/e2e/creation.spec.ts`
- Create: `mingjing-content-platform/frontend/e2e/publishing.spec.ts`
- Create: `mingjing-content-platform/frontend/playwright.config.ts`
- Create: `mingjing-content-platform/backend/tests/integration/test_full_workflow.py`
- Create: `mingjing-content-platform/docs/operations.md`
- Modify: `mingjing-content-platform/compose.yaml`
- Create: `mingjing-content-platform/README.md`

**Interfaces:**
- Consumes: all phase-one APIs and screens.
- Produces: reproducible local environment, backup/restore procedure, and tested primary workflow.

- [ ] **Step 1: Write failing end-to-end workflow tests**

```ts
test("administrator creates and prepares six-platform content", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel("用户名").fill("admin")
  await page.getByLabel("密码").fill("correct-password")
  await page.getByRole("button", { name: "登录" }).click()
  await page.getByLabel("推广要求").fill("面向礼品包装采购商，突出环保棉绳定制")
  await page.getByRole("button", { name: "生成六个平台内容" }).click()
  await expect(page.getByRole("tab", { name: "小红书" })).toBeVisible()
  await expect(page.getByRole("tab", { name: "公众号" })).toBeVisible()
})
```

- [ ] **Step 2: Run end-to-end tests and record real failures**

Run: `cd mingjing-content-platform; docker compose up -d --build`  
Expected: all services become healthy.

Run: `cd mingjing-content-platform/frontend; pnpm playwright test`  
Expected initially: FAIL until selectors, fixtures, and async status behavior are completed.

- [ ] **Step 3: Complete test fixtures and fix only observed workflow gaps**

Use mock AI, image, and publisher adapters in E2E mode. Cover desktop `1440x900` and mobile `390x844`, checking for horizontal overflow and overlapping controls.

- [ ] **Step 4: Document exact setup, secrets, provider configuration, backup, restore, and upgrade commands**

`operations.md` must include PostgreSQL backup and restore commands, object-storage backup location, administrator reset command, log locations, and official publishing authorization checklist.

- [ ] **Step 5: Run the complete verification suite**

Run: `cd mingjing-content-platform/backend; pytest -q`  
Expected: PASS.

Run: `cd mingjing-content-platform/frontend; pnpm vitest run; pnpm tsc --noEmit; pnpm playwright test`  
Expected: PASS.

Run: `cd mingjing-content-platform; docker compose ps`  
Expected: web, api, worker, database, and redis are healthy or running.

- [ ] **Step 6: Perform visual QA**

Capture the creation page and publishing center at desktop and mobile widths. Confirm real content is visible, navigation is usable, buttons and text do not overlap, and manual/automatic publishing remain discoverable.

- [ ] **Step 7: Commit**

```bash
git add mingjing-content-platform
git commit -m "test: verify Mingjing phase-one workflows"
```

## Final Acceptance Checklist

- [ ] A non-technical administrator can log in and manage company and product data.
- [ ] Product originals upload safely and image-analysis results are editable before use.
- [ ] One request produces editable, versioned outputs for all six platforms.
- [ ] Trend structures retain provenance and do not expose copied source text as templates.
- [ ] Cover and supporting images retain source and generation provenance.
- [ ] Manual and automatic publishing appear together; unauthorized automation falls back clearly.
- [ ] No password, API key, raw session token, or platform token is exposed to the browser or logs.
- [ ] Model and platform failures preserve successful content and offer retry or manual alternatives.
- [ ] Desktop and mobile E2E tests pass without layout overlap or horizontal overflow.
- [ ] Scheme C interfaces are declared but do not add premature implementation scope.
- [ ] Cloud deployment, backup, restore, and administrator recovery are documented.
