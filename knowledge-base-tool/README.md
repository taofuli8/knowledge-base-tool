# 知识库工具 (Knowledge Base Tool)

一个轻量级的知识库管理工具，用于收集、管理和检索 URL/教程/GitHub 项目。支持 Web 界面手动录入条目，并通过 AI 代理自动生成摘要。

## 项目定位

本项目旨在为开发者和 AI 代理提供一个**本地化的知识管理中枢**，解决以下痛点：

- 看到好的 GitHub 项目、教程、技术文章，收藏后遗忘
- 书签堆积如山，无法快速检索和回顾
- 需要向 AI 代理（如 OpenClaw）批量投喂参考材料时，缺乏结构化管理工具

通过将知识条目化、标签化、可搜索化，配合 AI 自动摘要能力，让知识管理从"收藏"进化为"可用"。

## 架构原理

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      Web 界面 (HTML/JS)                   │
│  新增条目 │ 搜索 │ 筛选 │ 标签浏览 │ 编辑 │ 详情查看       │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP 请求
┌──────────────────────────▼──────────────────────────────┐
│                   FastAPI 后端服务                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ CRUD 层  │  │ 搜索层   │  │ 标签层   │  │ AI 处理层│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
└───────┼─────────────┼─────────────┼─────────────┼──────┘
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────┐
│                  SQLite 数据库                           │
│  ┌──────────────┐  ┌──────────────────────────────────┐ │
│  │ entries 表   │  │ entries_fts (FTS5 全文索引)       │ │
│  │ - id, title  │  │ - 自动同步 entries 表的 title,    │ │
│  │ - url, type  │  │   summary, raw_content, tags      │ │
│  │ - summary    │  │   字段，支持高效全文检索            │ │
│  │ - tags(JSON) │  └──────────────────────────────────┘ │
│  │ - status     │                                       │
│  │ - timestamps │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### 数据流转

1. **录入阶段**: 用户通过 Web 界面或 API 新增条目，状态默认为 `pending`（待处理）
2. **处理阶段**: AI 代理（如 OpenClaw）读取 `pending` 状态的条目，访问 URL 获取内容，生成摘要后更新 `summary` 字段，状态改为 `completed`
3. **使用阶段**: 用户通过关键词搜索、类型筛选、标签过滤快速定位知识条目
4. **维护阶段**: 支持编辑、删除、更新标签等操作

### 核心设计

| 组件 | 说明 |
|------|------|
| **FTS5 全文索引** | SQLite 内置的全文搜索引擎，支持中文分词，可检索标题、摘要、原始内容 |
| **JSON 标签存储** | 标签以 JSON 数组格式存储在单个字段中，灵活扩展 |
| **状态机驱动** | 条目生命周期：`pending` → `processing` → `completed` / `failed` |
| **无前端构建** | 服务端渲染 HTML，零前端依赖，部署即用 |
| **REST API** | 完整的 CRUD + 搜索 + 统计接口，支持第三方集成 |

### 状态流转图

```
pending ──→ processing ──→ completed
   │            │
   │            └──→ failed
   └──→ deleted（软删除）
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python3 run.py
```

服务默认运行在 `http://localhost:8000`

### 3. 访问 Web 界面

打开浏览器访问 `http://localhost:8000`

## 详细使用指南

### 手动录入条目

**适用场景**: 浏览网页时发现有价值的内容，立即记录到知识库。

**操作步骤**:

1. 点击右上角绿色 **"新增"** 按钮
2. 填写表单：
   - **标题**: 条目名称（必填，如 "OpenClaw 官方文档"）
   - **URL**: 链接地址（可选，如 `https://github.com/example/repo`）
   - **类型**: 选择分类
     - `GitHub`: GitHub 项目链接
     - `链接`: 普通网页链接
     - `教程`: 教程、指南类内容
   - **简介**: 简短描述（可选，如 "OpenClaw 的完整使用文档和 API 参考"）
   - **标签**: 多个标签用英文逗号分隔（如 `AI, 自动化, 工具`）
3. 点击 **"保存"**
4. 条目自动进入 **"待处理"** 状态，等待 AI 摘要生成

**录入技巧**:

- 标题尽量简短明确，便于后续搜索
- 标签使用通用分类词，避免过于细粒度（如用 `Python` 而非 `Python3.11特定技巧`）
- URL 类型建议填写完整的 `https://` 地址

### 通知 AI 处理待处理条目

**适用场景**: 批量录入后，希望 AI 自动访问链接、阅读内容并生成摘要。

**单条处理**:

```bash
curl -X POST http://localhost:8000/api/entries/{id}/process
```

**批量处理所有待处理条目**:

```bash
curl -X POST http://localhost:8000/api/entries/process-pending
```

**处理流程**:

1. AI 代理读取状态为 `pending` 的条目
2. 访问条目的 URL，抓取页面内容
3. 使用大模型对内容进行摘要生成
4. 更新 `summary` 字段，状态改为 `completed`
5. 如果抓取或摘要失败，状态改为 `failed`

> 注：需要配置 AI 代理相关的环境变量（如 `OPENAI_API_KEY`）才能使用自动摘要功能。

### 搜索与检索

**全文搜索**:

在搜索框输入任意关键词，系统会同时搜索标题、摘要、原始内容。支持：

- 中文分词搜索（如输入 "自动化" 可匹配包含该词的条目）
- 多词搜索（空格分隔，如 `Python 自动化`）
- 精确匹配（引号包裹，如 `"FastAPI"`）

**类型筛选**:

通过下拉菜单筛选：
- 全部类型
- GitHub
- 链接
- 教程

**标签筛选**:

- 点击任意标签，列表自动过滤包含该标签的条目
- 支持多选（点击多个标签，取交集）
- 标签过多时默认显示前 20 个，点击 **"展开"** 查看全部
- 已选中的标签会高亮显示，再次点击取消

**组合筛选**:

搜索关键词 + 类型 + 标签可以同时使用，实现精确筛选。例如：搜索 "API" + 选择 GitHub 类型 + 选中 "自动化" 标签。

### 查看与编辑条目

**查看详情**:

1. 点击任意条目卡片
2. 弹窗显示：
   - 标题、类型、状态、创建时间
   - 摘要内容
   - 标签列表
   - 原始内容（前 3000 字符）
   - 操作按钮（编辑、删除、打开链接）

**编辑条目**:

1. 在详情弹窗中点击 **"编辑"**
2. 修改标题、简介、标签
3. 点击 **"保存"** 生效
4. 点击 **"取消"** 关闭编辑模式

**删除条目**:

- 点击 **"删除"** 按钮，确认后软删除（标记为 deleted，不真正删除数据库记录）

### 数据统计

页面顶部展示四个统计卡片：

- **总计**: 所有有效条目数量
- **GitHub**: GitHub 类型条目数量
- **链接**: 链接类型条目数量
- **教程**: 教程类型条目数量

## 使用技能与技巧

### 批量导入

如果有现成的数据源（如 JSON 文件、浏览器书签导出文件），可以使用 `import_kb.py` 脚本批量导入：

```bash
python3 import_kb.py --file data.json
```

### API 集成

本项目提供完整的 REST API，可以与其他工具集成：

**浏览器扩展联动**:

通过 API 将浏览器书签自动同步到知识库：

```bash
curl -X POST http://localhost:8000/api/entries \
  -H "Content-Type: application/json" \
  -d '{
    "title": "网页标题",
    "url": "https://example.com",
    "content_type": "url",
    "tags": ["收藏", "待读"]
  }'
```

**定时摘要生成**:

使用 cron 或 systemd timer 定期触发 AI 摘要生成：

```bash
# 每天凌晨 2 点处理待处理条目
0 2 * * * curl -s -X POST http://localhost:8000/api/entries/process-pending
```

**与 OpenClaw 集成**:

OpenClaw 可以通过 API 读取知识库中的条目，作为上下文参考：

```bash
# 获取与某个主题相关的条目
curl "http://localhost:8000/api/search?q=Python&content_type=tutorial"
```

### 标签管理建议

**推荐标签体系**:

| 层级 | 示例 |
|------|------|
| 技术栈 | `Python`, `JavaScript`, `Go`, `React` |
| 领域 | `AI`, `自动化`, `Web开发`, `运维` |
| 用途 | `工具`, `教程`, `框架`, `库` |
| 优先级 | `必读`, `参考`, `灵感` |

**标签命名规范**:

- 使用中文或英文，保持一致性
- 避免同义词混用（如统一用 `Python` 而非混用 `python`, `py`）
- 控制在 20 个常用标签以内，避免过于分散

### 性能优化

**大数据量场景**:

- 当条目超过 1000 条时，建议定期运行 VACUUM 优化数据库：
  ```bash
  sqlite3 knowledge.db "VACUUM;"
  ```
- 如果搜索变慢，可以重建 FTS5 索引：
  ```bash
  sqlite3 knowledge.db "INSERT INTO entries_fts(entries_fts) VALUES('rebuild');"
  ```

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整的 OpenAPI 文档（Swagger UI）。

### 主要接口

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| GET | `/` | Web 界面 | - |
| POST | `/api/entries` | 新增条目 | `{"title", "url", "content_type", "summary", "tags"}` |
| GET | `/api/entries` | 获取条目列表 | 查询参数 `page`, `page_size`, `content_type` |
| GET | `/api/entries/{id}` | 获取单个条目详情 | - |
| PUT | `/api/entries/{id}` | 更新条目 | `{"title", "summary", "tags", "url"}` |
| DELETE | `/api/entries/{id}` | 删除条目 | - |
| GET | `/api/search` | 全文搜索 | 查询参数 `q`, `page`, `content_type`, `tags` |
| GET | `/api/tags` | 获取所有标签 | - |
| GET | `/api/stats` | 获取统计数据 | - |

### 响应格式

**成功响应**:

```json
{
  "id": 1,
  "title": "示例条目",
  "url": "https://example.com",
  "content_type": "url",
  "summary": "自动生成的摘要内容",
  "tags": ["标签1", "标签2"],
  "status": "completed",
  "created_at": "2026-05-14 10:00:00",
  "updated_at": "2026-05-14 10:05:00"
}
```

**错误响应**:

```json
{
  "detail": "错误描述信息"
}
```

## 项目结构

```
knowledge-base-tool/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口 + Web 界面渲染
│   ├── database.py      # SQLite 数据库初始化与 FTS5 配置
│   ├── crud.py          # 数据库 CRUD 操作封装
│   └── models.py        # Pydantic 数据模型定义
├── run.py               # 服务启动脚本
├── requirements.txt     # Python 依赖列表
├── import_kb.py         # 批量数据导入脚本
├── README.md            # 项目文档（本文件）
└── knowledge.db         # SQLite 数据库文件（运行后生成）
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库文件路径 | `./knowledge.db` |
| `OPENAI_API_KEY` | AI 摘要生成所需 API Key | 无 |
| `OPENAI_BASE_URL` | AI API 基础 URL | `https://api.openai.com/v1` |

### 数据库初始化

首次运行时，系统自动创建以下对象：

- `entries` 表：存储知识条目
- `entries_fts` 表：FTS5 全文索引（自动与 entries 表同步）

## 常见问题

**Q: 搜索中文不生效？**

A: SQLite FTS5 默认使用空格分词，中文需要确保内容已正确存储为 UTF-8 编码。如果分词效果不佳，可以在搜索时使用更长的关键词。

**Q: 如何备份数据？**

A: 直接复制 `knowledge.db` 文件即可。也可以使用 SQLite 的备份命令：
```bash
sqlite3 knowledge.db ".backup knowledge_backup.db"
```

**Q: 部署到服务器需要注意什么？**

A: 建议使用反向代理（如 Nginx）转发请求，并配置 HTTPS。数据库文件注意文件权限，确保运行用户有读写权限。

**Q: 如何重置数据库？**

A: 删除 `knowledge.db` 文件后重启服务，系统会自动重新初始化空数据库。

## License

MIT
