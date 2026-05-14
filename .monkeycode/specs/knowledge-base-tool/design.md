# 知识库管理工具

Feature Name: knowledge-base-tool
Updated: 2026-05-14

## Description

一个基于 Python + SQLite 的知识库管理工具，提供 REST API 供 AI Agent 调用。支持三种内容类型入库（URL 链接、教程文案、GitHub 项目），具备全文搜索、标签分类、内容抓取辅助等功能。

## Architecture

```mermaid
graph TD
    A[用户] -->|提交内容| B[REST API 层]
    C[AI Agent] -->|调用 API| B
    B --> D[业务逻辑层]
    D --> E[SQLite 数据库]
    D --> F[内容抓取模块]
    F --> G[网页抓取]
    F --> H[GitHub API]
    D --> I[全文搜索 FTS5]
    I --> E
```

系统采用三层架构：

1. **REST API 层**: 使用 FastAPI 框架提供 HTTP 接口
2. **业务逻辑层**: 处理条目 CRUD、搜索、标签管理
3. **数据层**: SQLite + FTS5 全文搜索引擎

## Components and Interfaces

### 1. FastAPI 应用

启动 HTTP 服务，监听默认端口 8000，提供以下路由：

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/entries` | 创建新条目 |
| GET | `/api/entries` | 列出条目（支持分页） |
| GET | `/api/entries/{id}` | 获取条目详情 |
| PUT | `/api/entries/{id}` | 更新条目 |
| DELETE | `/api/entries/{id}` | 删除条目 |
| GET | `/api/entries/search` | 搜索条目 |
| GET | `/api/entries/{id}/content` | 获取条目原始内容（供 Agent 抓取） |
| POST | `/api/entries/{id}/summary` | 更新条目简介 |
| GET | `/api/tags` | 获取所有标签 |

### 2. 数据库模型

```
Entry:
  - id: INTEGER PRIMARY KEY
  - title: TEXT (标题)
  - url: TEXT (原始 URL，可选)
  - content_type: TEXT (url/tutorial/github)
  - raw_content: TEXT (原始内容，供 Agent 生成简介)
  - summary: TEXT (Agent 生成的简介)
  - tags: TEXT (JSON 数组存储标签)
  - status: TEXT (pending/processed/deleted)
  - created_at: TIMESTAMP
  - updated_at: TIMESTAMP
```

### 3. 内容抓取模块

- **网页抓取**: 使用 `httpx` + `trafilatura` 提取网页正文
- **GitHub 抓取**: 使用 GitHub REST API 获取仓库信息和 README

### 4. 全文搜索模块

使用 SQLite FTS5 虚拟表，对 `title`、`summary`、`raw_content`、`tags` 建立全文索引。

## Data Models

### EntryCreate (请求体)

```json
{
  "url": "https://...",           // 可选，URL 类型必填
  "content_type": "url|tutorial|github",
  "raw_content": "...",           // 可选，tutorial 类型必填
  "title": "..."                  // 可选，未提供时从 URL 提取
}
```

### EntryUpdate (请求体)

```json
{
  "title": "...",
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "url": "..."
}
```

### EntryResponse (响应体)

```json
{
  "id": 1,
  "title": "...",
  "url": "https://...",
  "content_type": "url",
  "summary": "...",
  "tags": ["tag1", "tag2"],
  "status": "processed",
  "created_at": "2026-05-14T10:00:00",
  "updated_at": "2026-05-14T10:00:00"
}
```

### SearchResponse (响应体)

```json
{
  "total": 10,
  "page": 1,
  "page_size": 20,
  "items": [EntryResponse, ...]
}
```

## Correctness Properties

1. 每个条目必须有唯一的 ID（自增主键）
2. `content_type` 必须是 `url`、`tutorial`、`github` 之一
3. 删除操作使用软删除（status 标记为 deleted），不物理删除数据
4. 搜索关键词至少匹配 title、summary、tags、url 中的一个字段
5. 标签数组在存储前必须去重
6. 分页参数 page >= 1, page_size 范围 1-100

## Error Handling

| 错误场景 | 处理方式 |
|----------|----------|
| 无效的 content_type | 返回 400 + 错误信息 |
| 条目不存在 | 返回 404 |
| 数据库连接失败 | 返回 500 + 错误信息 |
| 内容抓取超时 | 返回错误信息，条目标记为异常 |
| 搜索关键词为空 | 返回空结果集 |
| 标签格式错误 | 返回 400 + 错误信息 |

## Test Strategy

1. **单元测试**: 使用 pytest 测试数据库操作、搜索逻辑、标签处理
2. **API 测试**: 使用 httpx 测试客户端验证所有 API 端点
3. **集成测试**: 验证完整工作流：创建条目 → 获取内容 → 更新简介 → 搜索
4. **边界测试**: 空数据库搜索、超长内容处理、特殊字符标签

## References

[^1]: FastAPI 官方文档 - https://fastapi.tiangolo.com/
[^2]: SQLite FTS5 文档 - https://www.sqlite.org/fts5.html
[^3]: httpx 文档 - https://www.python-httpx.org/
[^4]: trafilatura 文档 - https://trafilatura.readthedocs.io/
