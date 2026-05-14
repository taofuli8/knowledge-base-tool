# 知识库管理系统 (Knowledge Base Management System)

一个完整的知识管理解决方案，包含 **Web 服务** 和 **AI 技能** 两个核心组件。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         知识库管理系统                            │
│                                                                 │
│  ┌──────────────────────────┐    ┌──────────────────────────┐   │
│  │   Web 服务项目           │    │   AI 技能项目            │   │
│  │   (knowledge-base-tool)  │◄──►│   (OpenClaw Skill)       │   │
│  │                          │    │                          │   │
│  │  • 条目管理 CRUD         │    │  • 自动抓取网页内容       │   │
│  │  • 全文搜索 (FTS5)       │    │  • AI 摘要生成           │   │
│  │  • 标签系统              │    │  • 批量处理待处理条目     │   │
│  │  • 数据导入/导出         │    │  • 状态更新管理          │   │
│  └──────────────────────────┘    └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 项目组成

### 1. Web 服务项目 (`knowledge-base-tool/`)

基于 Python + FastAPI + SQLite 构建的轻量级 Web 应用，提供知识条目的录入、搜索、管理和展示功能。

**核心功能**:
- 全中文 Web 界面
- 手动录入条目（标题、URL、类型、简介、标签）
- SQLite FTS5 全文检索
- 标签筛选与折叠展示
- 数据统计面板
- REST API 支持

**技术栈**:
- 后端: Python 3.9+, FastAPI
- 数据库: SQLite + FTS5 全文索引
- 前端: 原生 HTML/CSS/JS（服务端渲染）
- 部署: 无外部依赖，单文件启动

**快速开始**:

```bash
cd knowledge-base-tool
pip install -r requirements.txt
python3 run.py
```

访问 `http://localhost:8000` 使用 Web 界面。

### 2. AI 技能项目 (OpenClaw Skill)

配合 Web 服务使用的 AI 技能，自动处理"待处理"状态的知识条目，完成内容抓取和摘要生成。

**工作流程**:

1. 用户在 Web 界面手动录入条目，状态为 `pending`（待处理）
2. 用户通知 AI 代理（如 OpenClaw）处理待处理条目
3. AI 技能读取条目 URL，抓取网页内容
4. 使用大模型生成内容摘要
5. 更新条目的 `summary` 字段，状态改为 `completed`

**集成方式**:

通过 REST API 与 Web 服务交互：

```bash
# 获取待处理条目
GET /api/entries?status=pending

# 更新条目摘要
PUT /api/entries/{id}
{
  "summary": "AI 生成的摘要内容",
  "tags": ["AI", "自动化"]
}
```

## 使用场景

### 场景一：个人知识收集

1. 浏览网页时发现有价值的内容
2. 打开知识库 Web 界面，点击"新增"录入条目
3. 填写标题、URL、标签
4. 点击保存，条目进入待处理队列

### 场景二：AI 辅助摘要生成

1. 批量录入多个待读链接
2. 通知 AI 代理处理待处理条目
3. AI 自动访问链接、阅读内容、生成摘要
4. 在 Web 界面查看生成的摘要，快速了解内容要点

### 场景三：知识检索与回顾

1. 通过关键词搜索全文
2. 使用标签筛选特定主题
3. 查看条目详情和 AI 生成的摘要
4. 点击"打开链接"访问原始内容

## 部署指南

### 本地开发

```bash
# 克隆项目
git clone https://github.com/taofuli8/knowledge-base-tool.git
cd knowledge-base-tool

# 安装依赖
pip install -r requirements.txt

# 启动服务
python3 run.py
```

### 服务器部署

```bash
# 上传项目到服务器
scp -r knowledge-base-tool/ user@server:/opt/

# 安装依赖
pip install -r requirements.txt

# 使用 systemd 管理
sudo nano /etc/systemd/system/kb-tool.service

[Unit]
Description=Knowledge Base Tool
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/knowledge-base-tool
ExecStart=/usr/bin/python3 run.py
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl enable kb-tool
sudo systemctl start kb-tool
```

### Docker 部署（可选）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python3", "run.py"]
```

```bash
docker build -t kb-tool .
docker run -d -p 8000:8000 -v $(pwd)/data:/app/data kb-tool
```

## API 文档

启动服务后访问 `http://localhost:8000/docs` 查看完整的 Swagger UI 文档。

主要接口：
- `POST /api/entries` - 新增条目
- `GET /api/entries` - 获取列表
- `GET /api/entries/{id}` - 获取详情
- `PUT /api/entries/{id}` - 更新条目
- `DELETE /api/entries/{id}` - 删除条目
- `GET /api/search` - 全文搜索
- `GET /api/tags` - 获取标签
- `GET /api/stats` - 统计数据

## 常见问题

**Q: 如何备份数据？**
A: 直接复制 `knowledge.db` 文件即可。

**Q: 支持多用户吗？**
A: 当前版本为单用户设计，如需多用户可扩展添加认证模块。

**Q: 中文搜索效果如何？**
A: 使用 SQLite FTS5，支持基本中文分词搜索。如需更精准的分词，可集成 jieba 等分词库。

**Q: AI 摘要生成失败怎么办？**
A: 检查 AI API Key 配置，查看服务日志获取详细错误信息。失败条目状态会标记为 `failed`，可重试处理。

## License

MIT
