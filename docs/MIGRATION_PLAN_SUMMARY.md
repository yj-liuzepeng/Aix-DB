# SQLBot Text2SQL 迁移计划摘要

## 📋 迁移概述

**源项目**: `/Users/lihuan/python-workspace/SQLBot`  
**目标项目**: 当前项目 `sanic-web`  
**迁移路径**: `agent/text2sql/` 目录下

## 🎯 迁移目标

1. ✅ **完全迁移所有 template 提示词模块**（8个模块）
2. ✅ **前端渲染改为 AntV 组件模式**（替代 G2-SSR）
3. ✅ **放入 `agent/text2sql/` 目录**
4. ✅ **复用现有功能**：数据源、用户、权限、术语、数据训练示例

## 📊 核心架构对比

| 维度 | SQLBot | sanic-web (当前) | 迁移方案 |
|------|--------|------------------|----------|
| Web框架 | FastAPI | Sanic | 保持 Sanic ✅ |
| 状态管理 | 函数式 | LangGraph | 保持 LangGraph ✅ |
| 模板系统 | YAML 文件 | 硬编码 | 迁移为 YAML 🔄 |
| 数据库规则 | 11种 | 仅 MySQL | 迁移全部 11种 🔄 |
| 图表渲染 | G2-SSR (图片) | AntV (前端) | 使用 AntV ✅ |
| RAG检索 | Embedding+pgvector | Neo4j | 增强 Embedding 🔄 |

## 📁 迁移模块清单

### 必须迁移的模板模块（8个）

1. ✅ **generate_sql** - SQL 生成提示词（核心）
2. ✅ **generate_chart** - 图表配置生成提示词
3. ✅ **select_datasource** - 数据源选择提示词
4. ✅ **generate_guess_question** - 推荐问题生成提示词
5. ✅ **filter/permissions** - 权限过滤提示词
6. ✅ **generate_dynamic** - 动态 SQL 提示词（可选）

**注意**: 不包含数据分析和数据预测功能

### 必须迁移的数据库规则（11种）

- PostgreSQL ✅
- MySQL ✅
- Oracle
- Microsoft SQL Server
- ClickHouse
- AWS Redshift
- Elasticsearch
- StarRocks
- Doris
- DM (达梦)
- Kingbase

## 🗂️ 新的目录结构

```
agent/text2sql/
├── template/                   # 🆕 模板系统
│   ├── template_loader.py      # YAML 加载器
│   ├── prompt_builder.py       # 提示词构建器
│   └── yaml/
│       ├── template.yaml       # 基础模板
│       └── sql_examples/       # 11种数据库规则
├── rag/                        # 🆕 RAG 检索
│   ├── table_retriever.py      # 表 Embedding 检索
│   ├── terminology_retriever.py # 术语检索
│   └── training_retriever.py   # 示例检索
├── permission/                 # 🆕 权限处理
│   ├── filter_injector.py      # 权限条件注入
│   └── permission_service.py   # 权限规则获取
├── chart/                      # 🆕 图表生成
│   └── generator.py            # 图表配置生成
├── analysis/                   # 增强
│   └── llm_summarizer.py       # 数据总结（已有，需增强）
└── sql/
    └── generator.py            # 完全重写（使用模板系统）
```

## 🔄 LangGraph 流程扩展

### 当前流程
```
schema_inspector → table_relationship → sql_generator → 
sql_executor → summarize → data_render
```

### 扩展后流程
```
schema_inspector 
  → [可选] datasource_selector
  → rag_enhancer (表/术语/示例检索)
  → table_relationship
  → sql_generator (使用模板系统)
  → [可选] permission_filter
  → sql_executor
  → summarize
  → chart_generator
  → data_render_condition
    ├─→ data_render (AntV)
    └─→ data_render_apache
```

## 📅 迁移阶段规划

### 🔴 阶段一：模板系统迁移（最高优先级）
**时间**: 3-4 天
- [ ] 迁移所有 YAML 模板文件
- [ ] 实现 `TemplateLoader` 和 `PromptBuilder`
- [ ] 重写 SQL 生成节点使用模板系统

### 🟡 阶段二：RAG 增强检索（高优先级）
**时间**: 2-3 天
- [ ] 实现表结构 Embedding 检索
- [ ] 复用现有术语/训练示例服务
- [ ] 集成 RAG 增强节点

### 🟡 阶段三：权限处理（高优先级）
**时间**: 2 天
- [ ] 复用现有权限服务
- [ ] 实现权限条件注入节点

### 🟡 阶段四：图表生成（高优先级）
**时间**: 3-4 天
- [ ] 实现图表配置生成节点
- [ ] 增强 AntV 前端组件
- [ ] 支持所有图表类型

### 🟢 阶段五：数据源选择与推荐（低优先级）
**时间**: 2 天
- [ ] 实现数据源选择节点
- [ ] 实现推荐问题生成

### 🟡 阶段六：测试与优化（高优先级）
**时间**: 3-4 天
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化

**总计**: 17-22 天

**注意**: 不包含数据分析和数据预测功能

## ⚠️ 关键技术点

### 1. pgvector 支持
- ❓ 当前项目是否已安装 pgvector？
- 📝 如未安装，需要新增支持（或使用替代方案）

### 2. 模板变量替换
- 📝 注意 YAML 模板中的 `{variable}` 格式
- 📝 转义使用 `{{` 和 `}}`

### 3. AntV 前端适配
- 📝 需要支持动态图表配置解析
- 📝 支持所有图表类型：column、bar、line、pie、table

### 4. 现有功能复用
- ✅ 数据源服务：`services/datasource_service.py`
- ✅ 用户服务：`services/user_service.py`
- ✅ 权限服务：`services/permission_service.py`
- ✅ 术语服务：`services/terminology_service.py`
- ✅ 训练示例：`services/data_training_service.py`

## ✅ 待确认事项

1. **pgvector 支持**: 是否已安装？如未安装是否同意新增？
2. **前端 AntV**: 是否已准备好支持动态图表配置？
3. **迁移优先级**: 是否同意优先完成阶段一、二、三、四？
4. **测试环境**: 是否有测试环境验证多数据库支持？

## 📄 详细报告

完整迁移报告请查看：`docs/MIGRATION_REPORT_SQLBOT.md`

---

**生成时间**: 2026-01-08  
**待用户确认后开始执行迁移** ✋

