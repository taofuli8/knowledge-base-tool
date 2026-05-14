# 知识库工具 (Knowledge Base Tool)

一个轻量级的知识库管理工具，用于收集、管理和检索 URL/教程/GitHub 项目。支持 Web 界面手动录入条目，并通过 AI 自动生成摘要。

## 功能特性

- **Web 界面管理**: 全中文界面，支持搜索、筛选、标签浏览
- **手动录入**: 支持在 Web 界面直接新增条目（标题、URL、类型、简介、标签）
- **自动摘要**: 新增条目默认状态为"待处理"，可通过 AI 代理自动生成摘要
- **全文搜索**: 基于 SQLite FTS5 的全文检索
- **标签系统**: 支持标签筛选和折叠展示
- **数据统计**: 按类型（GitHub/链接/教程）统计条目数量
- **API 接口**: 完整的 REST API 支持

## 技术栈

- Python 3.9+
- FastAPI
- SQLite + FTS5
- 原生 HTML/CSS/JS（无前端构建依赖）

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

## 使用指南

### 手动录入条目

1. 点击右上角 **"新增"** 按钮
2. 填写以下信息：
   - **标题**: 条目名称（必填）
   - **URL**: 链接地址（可选）
   - **类型**: GitHub / 链接 / 教程
   - **简介**: 简短描述（可选）
   - **标签**: 多个标签用逗号分隔（可选）
3. 点击 **"保存"**，条目状态自动设为 **"待处理"**

### 通知 AI 处理待处理条目

新增的条目状态为 **"待处理"** 时，可通过以下接口触发 AI 摘要生成：

```bash
curl -X POST http://localhost:8000/api/entries/{id}/process
```

或批量处理所有待处理条目：

```bash
curl -X POST http://localhost:8000/api/entries/process-pending
```

> 注：需要配置 AI 代理相关的环境变量（如 API Key）才能使用自动摘要功能。

### 搜索与筛选

- **关键词搜索**: 在搜索框输入关键词，支持全文检索
- **类型筛选**: 通过下拉菜单筛选 GitHub/链接/教程
- **标签筛选**: 点击标签进行筛选，支持多选

### 编辑与删除

1. 点击任意条目卡片查看详情
2. 点击 **"编辑"** 修改标题、简介、标签
3. 点击 **"删除"** 移除条目

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整的 OpenAPI 文档。

### 主要接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | Web 界面 |
| POST | `/api/entries` | 新增条目 |
| GET | `/api/entries` | 获取条目列表 |
| GET | `/api/entries/{id}` | 获取单个条目详情 |
| PUT | `/api/entries/{id}` | 更新条目 |
| DELETE | `/api/entries/{id}` | 删除条目 |
| GET | `/api/search` | 全文搜索 |
| GET | `/api/tags` | 获取所有标签 |
| GET | `/api/stats` | 获取统计数据 |

## 项目结构

```
knowledge-base-tool/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 应用入口 + Web 界面
│   ├── database.py      # SQLite 数据库初始化
│   ├── crud.py          # 数据库 CRUD 操作
│   └── models.py        # Pydantic 数据模型
├── run.py               # 启动脚本
├── requirements.txt     # Python 依赖
├── import_kb.py         # 数据导入脚本
└── knowledge.db         # SQLite 数据库（运行后生成）
```

## 配置

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库路径 | `./knowledge.db` |
| `OPENAI_API_KEY` | AI 摘要生成所需 API Key | 无 |
| `OPENAI_BASE_URL` | AI API 基础 URL | `https://api.openai.com/v1` |

## License

MIT
