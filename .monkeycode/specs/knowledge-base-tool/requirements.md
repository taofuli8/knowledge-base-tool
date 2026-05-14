# Requirements Document

## Introduction

知识库管理工具（Knowledge Base Tool）为 AI Agent 提供结构化的知识入库和检索能力。用户通过多种方式提交内容（网址、教程文案、GitHub 地址），AI Agent 负责抓取内容并生成结构化简介后入库。用户需要时可通过搜索快速定位已存储的项目。

## Glossary

- **知识库条目**: 存储在知识库中的单条知识记录，包含 URL、标题、简介、标签、分类等元数据
- **Agent**: 使用知识库工具的 AI 助手（如 openclaw）
- **入库**: 将内容解析、生成简介后存储到知识库的过程
- **条目类型**: URL 链接、教程文案、GitHub 项目
- **FTS**: Full-Text Search，全文搜索

## Requirements

### Requirement 1: 条目创建与入库

**User Story:** AS 用户，我希望通过多种方式提交内容到知识库，so that 我的知识可以被系统化管理和检索

#### Acceptance Criteria

1. WHEN 用户提交一个普通网址，知识库工具 SHALL 返回该网址的原始信息，供 Agent 抓取内容
2. WHEN 用户提交一段教程文案，知识库工具 SHALL 将文案内容存储为条目，并标记类型为 "tutorial"
3. WHEN 用户提交一个 GitHub 仓库地址，知识库工具 SHALL 识别该地址为 GitHub 类型，并提供仓库元数据获取接口
4. WHEN Agent 提交条目简介信息，知识库工具 SHALL 将简介与对应条目关联存储
5. WHEN 条目创建成功，知识库工具 SHALL 返回条目的唯一 ID

### Requirement 2: 内容抓取辅助

**User Story:** AS Agent，我希望获取待处理条目的原始内容，so that 我可以生成结构化的简介

#### Acceptance Criteria

1. WHEN Agent 请求获取某个 URL 条目的原始内容，知识库工具 SHALL 返回该 URL 指向的网页内容（纯文本格式）
2. WHEN Agent 请求获取某个 GitHub 仓库的 README，知识库工具 SHALL 返回该仓库的 README 内容
3. WHEN 内容抓取失败，知识库工具 SHALL 返回错误信息，供 Agent 重试或标记异常
4. IF 网页内容超过 50000 字符，知识库工具 SHALL 返回截断后的内容并标记是否需要继续获取

### Requirement 3: 简介生成与更新

**User Story:** AS Agent，我希望将生成的简介保存到条目中，so that 用户可以快速了解条目内容

#### Acceptance Criteria

1. WHEN Agent 提交条目简介，知识库工具 SHALL 将简介文本存储到对应条目中
2. WHEN Agent 更新条目简介，知识库工具 SHALL 覆盖原有简介内容
3. WHEN 条目包含简介，知识库工具 SHALL 在搜索结果中展示简介内容
4. IF Agent 提交的简介超过 2000 字符，知识库工具 SHALL 截断并保留前 2000 字符

### Requirement 4: 搜索与检索

**User Story:** AS 用户，我希望通过关键词搜索知识库，so that 我可以快速找到相关的项目和内容

#### Acceptance Criteria

1. WHEN 用户输入搜索关键词，知识库工具 SHALL 在条目的标题、简介、URL、标签中进行全文匹配
2. WHEN 搜索结果返回，知识库工具 SHALL 按相关度排序返回匹配条目
3. IF 搜索关键词匹配到多个条目，知识库工具 SHALL 返回所有匹配结果，限制单次最多 50 条
4. WHEN 用户使用标签过滤搜索，知识库工具 SHALL 仅返回包含指定标签的条目
5. WHEN 用户使用类型过滤搜索，知识库工具 SHALL 仅返回指定类型的条目（url/tutorial/github）

### Requirement 5: 条目管理

**User Story:** AS 用户，我希望管理知识库中的条目，so that 我可以维护知识库的质量

#### Acceptance Criteria

1. WHEN 用户请求查看条目详情，知识库工具 SHALL 返回该条目的完整信息（标题、简介、URL、类型、标签、创建时间、更新时间）
2. WHEN 用户更新条目标签，知识库工具 SHALL 替换原有标签列表
3. WHEN 用户删除条目，知识库工具 SHALL 标记为删除状态，实际数据保留 30 天后可恢复
4. WHEN 用户列出所有条目，知识库工具 SHALL 支持分页返回，每页默认 20 条

### Requirement 6: 标签系统

**User Story:** AS 用户，我希望为条目添加标签，so that 我可以通过标签分类和过滤知识

#### Acceptance Criteria

1. WHEN Agent 或用户为条目添加标签，知识库工具 SHALL 将标签存储为字符串数组
2. WHEN 用户请求获取所有标签，知识库工具 SHALL 返回知识库中所有使用过的标签及对应的条目数量
3. IF 用户提交重复标签，知识库工具 SHALL 自动去重
4. WHEN 用户通过标签搜索，知识库工具 SHALL 支持多标签组合查询（AND 逻辑）

### Requirement 7: API 接口

**User Story:** AS Agent，我希望通过 HTTP API 与知识库交互，so that 我可以远程调用知识库功能

#### Acceptance Criteria

1. WHEN Agent 发起 HTTP 请求，知识库工具 SHALL 提供 RESTful API 接口
2. WHEN Agent 提交 JSON 格式的数据，知识库工具 SHALL 解析并返回 JSON 格式响应
3. IF API 请求参数错误，知识库工具 SHALL 返回 400 状态码和错误描述
4. IF API 请求访问不存在的资源，知识库工具 SHALL 返回 404 状态码

### Requirement 8: 服务运行

**User Story:** AS 用户，我希望知识库服务可以在本地启动，so that Agent 可以通过网络调用

#### Acceptance Criteria

1. WHEN 用户启动服务，知识库工具 SHALL 在本地启动 HTTP 服务器
2. WHEN 服务启动，知识库工具 SHALL 自动创建或连接 SQLite 数据库文件
3. WHILE 服务运行，知识库工具 SHALL 保持数据库连接活跃
4. IF 数据库文件不存在，知识库工具 SHALL 自动初始化数据库表结构
