# SQLBot 项目 Text2SQL 模块迁移报告与计划

## 一、项目架构分析

### 1.1 SQLBot 项目架构

#### 技术栈
- **后端框架**: FastAPI
- **ORM**: SQLModel / SQLAlchemy  
- **LLM框架**: LangChain
- **状态管理**: 传统函数式（非 LangGraph）
- **数据库**: PostgreSQL + pgvector（向量存储）
- **图表渲染**: G2-SSR 服务（生成图片）

#### Text2SQL 核心流程架构

```
用户问题输入
    ↓
1. 数据源选择（如未指定）
   - Embedding 检索最相关数据源
   - LLM 智能选择
    ↓
2. RAG 增强检索
   ├─ 表结构 Embedding 检索（Top-K 表选择）
   ├─ 术语库 Embedding 检索（业务术语匹配）
   └─ 数据训练示例检索（相似问题-SQL示例）
    ↓
3. 提示词构建（YAML 模板系统）
   ├─ 系统提示词加载（template.yaml）
   ├─ 数据库特定规则（sql_examples/*.yaml）
   ├─ 术语信息注入
   ├─ 示例信息注入
   ├─ 历史对话上下文注入
   └─ 自定义提示词注入
    ↓
4. LLM SQL 生成
   ├─ 流式调用 LLM
   ├─ SQL 解析与提取（JSON格式）
   └─ SQL 验证
    ↓
5. 权限处理
   ├─ 行级权限规则获取
   ├─ 列级权限规则获取
   └─ SQL 权限条件注入
    ↓
6. SQL 执行
   ├─ 连接数据源
   ├─ 执行 SQL 查询
   └─ 结果格式化
    ↓
7. 结果处理
   ├─ 图表生成（G2-SSR）
   └─ 图表配置生成（LLM）
    ↓
结果返回给用户
```

#### 核心模板模块

SQLBot 项目包含以下提示词模板模块：

1. **generate_sql** - SQL 生成提示词
   - 基础模板：`template.yaml` 中的 `template.sql`
   - 数据库特定规则：`sql_examples/*.yaml`（支持 11 种数据库）
   - 包含：系统提示词、规则、示例、术语/示例注入

2. **generate_chart** - 图表配置生成提示词
   - 基于 SQL 和问题生成图表配置（JSON）
   - 支持：table、column、bar、line、pie

3. **select_datasource** - 数据源选择提示词
   - LLM 智能选择最相关的数据源

4. **generate_guess_question** - 推荐问题生成提示词
   - 基于表结构和历史问题推荐问题

5. **filter/permissions** - 权限过滤提示词
   - 将行级/列级权限条件注入 SQL

6. **generate_dynamic** - 动态 SQL 生成提示词
   - 处理动态数据源场景（可选）

### 1.2 当前项目（sanic-web）架构

#### 技术栈
- **后端框架**: Sanic
- **ORM**: SQLAlchemy
- **LLM框架**: LangChain
- **状态管理**: LangGraph StateGraph
- **数据库**: PostgreSQL + Neo4j（表关系）
- **图表渲染**: AntV + Apache ECharts

#### 当前 Text2SQL 流程（LangGraph）

```
schema_inspector（表结构检索）
    ↓
table_relationship（Neo4j 表关系）
    ↓
sql_generator（SQL 生成 - 简单提示词）
    ↓
sql_executor（SQL 执行）
    ↓
summarize（数据总结）
    ↓
data_render_condition（条件判断）
    ├─→ data_render（AntV 图表）
    └─→ data_render_apache（Apache 表格）
```

#### 已有功能模块

✅ **已完成**:
- 数据源管理（`services/datasource_service.py`）
- 用户管理（`services/user_service.py`）
- 权限管理（`services/permission_service.py`）
- 术语管理（`services/terminology_service.py`）
- 数据训练示例（`services/data_training_service.py`）
- LangGraph 状态图架构
- AntV 图表渲染组件

❌ **待迁移**:
- SQLBot 完整的模板系统（YAML）
- 多数据库特定规则
- RAG 增强检索逻辑
- 权限注入逻辑
- 图表配置生成
- 数据源智能选择
- 推荐问题生成

### 1.3 架构差异对比

| 维度 | SQLBot | sanic-web (当前) | 迁移适配方案 |
|------|--------|------------------|--------------|
| Web框架 | FastAPI | Sanic | ✅ 保持 Sanic |
| 状态管理 | 函数式 | LangGraph | ✅ 保持 LangGraph，增强节点功能 |
| 模板系统 | YAML 文件 | 硬编码字符串 | 🔄 迁移为 YAML + Python 加载 |
| 数据库规则 | 11种数据库 YAML | 仅 MySQL | 🔄 迁移所有数据库规则 |
| RAG检索 | Embedding + pgvector | Neo4j 表关系 | 🔄 增强 Embedding 检索，保留 Neo4j |
| 图表渲染 | G2-SSR (图片) | AntV (前端) | ✅ 使用 AntV（要求） |
| 权限注入 | LLM 生成过滤 SQL | 未实现 | 🔄 迁移权限注入逻辑 |
| 提示词模块 | 8个独立模块 | 1个简单模块 | 🔄 全部迁移 |

## 二、迁移方案设计

### 2.1 迁移目标

1. ✅ **完全迁移所有 template 提示词模块**并适配当前 LangGraph 架构
2. ✅ **前端渲染改为 AntV 组件模式**（替代 G2-SSR 图片生成）
3. ✅ **放入 `agent/text2sql` 目录**下
4. ✅ **复用现有功能**：数据源、用户、权限、术语、数据训练示例

### 2.2 目录结构设计

```
agent/text2sql/
├── __init__.py
├── text2_sql_agent.py          # 主 Agent（已有，需增强）
├── state/
│   ├── agent_state.py          # 状态定义（已有，需扩展）
│   └── __init__.py
├── database/
│   ├── db_service.py           # 数据库服务（已有，需增强）
│   ├── neo4j_search.py         # Neo4j 表关系（已有）
│   └── embedding_search.py     # 新增：Embedding 检索
├── sql/
│   ├── generator.py            # SQL 生成节点（需完全重写）
│   └── __init__.py
├── template/                   # 新增：模板系统
│   ├── __init__.py
│   ├── template_loader.py      # YAML 模板加载器
│   ├── prompt_builder.py       # 提示词构建器
│   └── yaml/                   # YAML 模板目录
│       ├── template.yaml       # 基础模板
│       └── sql_examples/       # 数据库特定规则
│           ├── PostgreSQL.yaml
│           ├── MySQL.yaml
│           ├── Oracle.yaml
│           └── ... (共11种)
├── chart/
│   ├── generator.py            # 新增：图表配置生成节点
│   └── __init__.py
├── analysis/
│   ├── llm_summarizer.py       # 已有，需增强
│   └── __init__.py
├── rag/                        # 新增：RAG 增强检索
│   ├── __init__.py
│   ├── table_retriever.py      # 表结构检索
│   ├── terminology_retriever.py # 术语检索
│   └── training_retriever.py   # 示例检索
├── permission/                 # 新增：权限处理
│   ├── __init__.py
│   ├── filter_injector.py      # 权限条件注入节点
│   └── permission_service.py   # 权限规则获取
├── datasource/                 # 新增：数据源选择
│   ├── __init__.py
│   └── selector.py             # 数据源选择节点
└── analysis/
    ├── graph.py                # 状态图定义（已有，需扩展）
    ├── data_render_antv.py     # AntV 渲染（已有）
    ├── data_render_apache.py   # Apache 表格（已有）
    └── __init__.py
```

### 2.3 LangGraph 状态图扩展设计

#### 新的状态图流程

```python
# 扩展后的 LangGraph 流程

schema_inspector              # 表结构检索（保留，增强 Embedding）
    ↓
[可选] datasource_selector    # 数据源选择（如果未指定）
    ↓
rag_enhancer                  # RAG 增强检索（新增）
    ├─→ table_embedding_retriever  # 表 Embedding 检索
    ├─→ terminology_retriever      # 术语检索
    └─→ training_retriever         # 示例检索
    ↓
table_relationship            # Neo4j 表关系（保留）
    ↓
sql_generator                 # SQL 生成（完全重写，使用模板系统）
    ↓
[可选] permission_filter      # 权限过滤（新增）
    ↓
sql_executor                  # SQL 执行（保留）
    ↓
summarize                     # 数据总结（保留）
    ↓
chart_generator               # 图表配置生成（新增）
    ↓
data_render_condition         # 条件判断（保留）
    ├─→ data_render           # AntV 图表渲染
    └─→ data_render_apache    # Apache 表格渲染
```

#### AgentState 状态扩展

```python
class AgentState(TypedDict):
    # 现有字段
    user_query: str
    db_info: Optional[Dict]
    table_relationship: Optional[List[Dict[str, Any]]]
    generated_sql: Optional[str]
    execution_result: Optional[ExecutionResult]
    report_summary: Optional[str]
    chart_type: Optional[str]
    apache_chart_data: Optional[Dict[str, Any]]
    datasource_id: Optional[int]
    
    # 新增字段
    selected_datasource_id: Optional[int]      # 选择的数据源ID
    rag_context: Optional[Dict[str, Any]]      # RAG 检索上下文
    terminology_context: Optional[str]         # 术语上下文
    training_examples: Optional[List[Dict]]    # 训练示例
    permission_filters: Optional[List[Dict]]   # 权限过滤条件
    filtered_sql: Optional[str]                # 权限过滤后的 SQL
    chart_config: Optional[Dict[str, Any]]     # 图表配置（AntV格式）
```

### 2.4 模板系统迁移设计

#### 模板加载器 (`template/template_loader.py`)

```python
class TemplateLoader:
    """YAML 模板加载器，支持缓存"""
    
    @staticmethod
    @cache
    def load_base_template() -> Dict[str, Any]:
        """加载基础模板 template.yaml"""
        
    @staticmethod
    @cache
    def load_sql_template(db_type: str) -> Dict[str, Any]:
        """加载数据库特定规则 sql_examples/{db_type}.yaml"""
        
    @staticmethod
    def reload_all_templates():
        """清空缓存，重新加载所有模板"""
```

#### 提示词构建器 (`template/prompt_builder.py`)

```python
class PromptBuilder:
    """提示词构建器，集成所有模块"""
    
    def build_sql_prompt(
        self,
        db_type: str,
        schema: str,
        question: str,
        terminologies: str,
        training_examples: str,
        custom_prompt: str,
        enable_limit: bool = True
    ) -> Tuple[str, str]:
        """构建 SQL 生成提示词（系统提示词 + 用户提示词）"""
        
    def build_chart_prompt(
        self,
        sql: str,
        question: str,
        chart_type: Optional[str] = None
    ) -> Tuple[str, str]:
        """构建图表配置生成提示词"""
        
    def build_datasource_prompt(
        self,
        question: str,
        datasource_list: List[Dict]
    ) -> Tuple[str, str]:
        """构建数据源选择提示词"""
        
    def build_permission_prompt(
        self,
        sql: str,
        filters: List[Dict]
    ) -> Tuple[str, str]:
        """构建权限过滤提示词"""
```

### 2.5 RAG 增强检索迁移设计

#### 表结构 Embedding 检索 (`rag/table_retriever.py`)

```python
class TableEmbeddingRetriever:
    """基于 Embedding 的表结构检索"""
    
    async def retrieve_tables(
        self,
        question: str,
        datasource_id: int,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        1. 计算问题的 Embedding
        2. 从 pgvector 中检索相似表结构
        3. 返回 Top-K 表及其结构
        """
```

#### 术语检索 (`rag/terminology_retriever.py`)

```python
class TerminologyRetriever:
    """术语库检索，复用现有术语服务"""
    
    async def retrieve_terminologies(
        self,
        question: str,
        datasource_id: Optional[int] = None,
        top_k: int = 10
    ) -> str:
        """
        1. 调用现有 terminology_service
        2. Embedding 或关键词匹配
        3. 格式化为模板所需的术语字符串
        """
```

#### 训练示例检索 (`rag/training_retriever.py`)

```python
class TrainingRetriever:
    """数据训练示例检索，复用现有服务"""
    
    async def retrieve_examples(
        self,
        question: str,
        datasource_id: Optional[int] = None,
        top_k: int = 5
    ) -> str:
        """
        1. 调用现有 data_training_service
        2. Embedding 匹配相似问题
        3. 格式化为模板所需的示例字符串
        """
```

### 2.6 权限处理迁移设计

#### 权限过滤注入节点 (`permission/filter_injector.py`)

```python
def permission_filter_injector(state: AgentState) -> AgentState:
    """
    权限过滤节点
    1. 调用现有 permission_service 获取行级/列级权限规则
    2. 使用 LLM 将权限条件注入 SQL
    3. 返回过滤后的 SQL
    """
    # 复用现有 permission_service
    from services.permission_service import get_user_permissions
    
    permissions = await get_user_permissions(
        datasource_id=state["datasource_id"],
        user_id=current_user.id
    )
    
    # 使用模板系统生成权限过滤提示词
    prompt = PromptBuilder().build_permission_prompt(
        sql=state["generated_sql"],
        filters=permissions
    )
    
    # 调用 LLM 生成过滤后的 SQL
    filtered_sql = await llm_call(prompt)
    
    state["filtered_sql"] = filtered_sql
    return state
```

### 2.7 图表生成迁移设计

#### AntV 图表配置生成 (`chart/generator.py`)

```python
def chart_generator(state: AgentState) -> AgentState:
    """
    图表配置生成节点
    1. 使用 LLM 根据 SQL 结果生成图表配置（JSON）
    2. 适配 AntV 组件格式
    3. 返回图表配置
    """
    sql_result = state["execution_result"].data
    chart_type = state.get("chart_type", "table")
    
    # 使用模板系统生成图表提示词
    prompt = PromptBuilder().build_chart_prompt(
        sql=state["generated_sql"],
        question=state["user_query"],
        chart_type=chart_type
    )
    
    # 调用 LLM 生成图表配置
    chart_config_json = await llm_call(prompt)
    
    # 解析 JSON，适配 AntV 格式
    chart_config = parse_antv_config(chart_config_json, sql_result)
    
    state["chart_config"] = chart_config
    return state
```

#### AntV 前端渲染适配

当前 `data_render_antv.py` 需要增强，支持：
- 接收 `chart_config`（包含 type、axis、series 等）
- 根据配置动态渲染对应的 AntV 图表组件
- 支持所有图表类型：column、bar、line、pie、table 等

### 2.8 数据库支持扩展

需要迁移的数据库规则 YAML 文件（11种）：
1. PostgreSQL.yaml ✅
2. MySQL.yaml ✅
3. Oracle.yaml
4. Microsoft_SQL_Server.yaml
5. ClickHouse.yaml
6. AWS_Redshift.yaml
7. Elasticsearch.yaml
8. StarRocks.yaml
9. Doris.yaml
10. DM.yaml
11. Kingbase.yaml

每个 YAML 包含：
- `quot_rule`: 引号规则（双引号/反引号/方括号）
- `limit_rule`: LIMIT 语法规则
- `other_rule`: 其他规则（别名、关键字冲突等）
- `basic_example`: 基础示例
- `example_answer_*`: 示例答案

## 三、迁移实施计划

### 阶段一：模板系统迁移（核心）

**优先级**: 🔴 最高

**任务清单**:
1. ✅ 创建 `agent/text2sql/template/` 目录结构
2. ✅ 迁移 `template.yaml` 基础模板
3. ✅ 迁移所有 11 种数据库 `sql_examples/*.yaml`
4. ✅ 实现 `TemplateLoader` 类（YAML 加载 + 缓存）
5. ✅ 实现 `PromptBuilder` 类（提示词构建）
6. ✅ 重写 `sql/generator.py` 使用模板系统
7. ✅ 测试 SQL 生成功能

**预估工作量**: 3-4 天

### 阶段二：RAG 增强检索迁移

**优先级**: 🟡 高

**任务清单**:
1. ✅ 实现 `rag/table_retriever.py`（表 Embedding 检索）
   - 需要 pgvector 支持（检查当前项目是否已有）
   - 表结构 Embedding 存储与检索
2. ✅ 实现 `rag/terminology_retriever.py`
   - 复用现有 `terminology_service`
   - 格式化为模板字符串
3. ✅ 实现 `rag/training_retriever.py`
   - 复用现有 `data_training_service`
   - 格式化为模板字符串
4. ✅ 创建 `rag_enhancer` 节点，整合三种检索
5. ✅ 更新 LangGraph 状态图，插入 RAG 节点

**预估工作量**: 2-3 天

### 阶段三：权限处理迁移

**优先级**: 🟡 高

**任务清单**:
1. ✅ 迁移 `template/filter/permissions` 提示词模板
2. ✅ 实现 `permission/permission_service.py`
   - 复用现有 `permission_service`
   - 获取行级/列级权限规则
3. ✅ 实现 `permission/filter_injector.py` 节点
   - 使用 LLM 注入权限条件到 SQL
4. ✅ 更新 LangGraph 状态图，插入权限过滤节点

**预估工作量**: 2 天

### 阶段四：图表生成迁移

**优先级**: 🟡 高

**任务清单**:
1. ✅ 迁移 `template/generate_chart` 提示词模板
2. ✅ 实现 `chart/generator.py` 节点
   - LLM 生成图表配置（JSON）
   - 适配 AntV 格式
3. ✅ 增强 `data_render_antv.py`
   - 支持动态图表配置渲染
   - 支持所有图表类型（column、bar、line、pie、table）
4. ✅ 更新前端 AntV 组件
   - 根据配置动态渲染对应图表类型
5. ✅ 更新 LangGraph 状态图，插入图表生成节点

**预估工作量**: 3-4 天

### 阶段五：数据源选择与推荐问题迁移

**优先级**: 🟢 低

**任务清单**:
1. ✅ 迁移 `template/select_datasource` 提示词模板
2. ✅ 迁移 `template/generate_guess_question` 提示词模板
3. ✅ 实现 `datasource/selector.py` 节点（数据源选择）
4. ✅ 实现 `question/recommender.py`（推荐问题生成）
5. ✅ 更新 LangGraph 状态图，添加可选节点

**预估工作量**: 2 天

### 阶段六：动态 SQL 与高级功能迁移（可选）

**优先级**: 🔵 低（可选）

**任务清单**:
1. ✅ 迁移 `template/generate_dynamic` 提示词模板
2. ✅ 实现动态数据源支持
3. ✅ 测试与优化

**预估工作量**: 2-3 天

### 阶段七：测试与优化

**优先级**: 🟡 高

**任务清单**:
1. ✅ 单元测试：每个节点独立测试
2. ✅ 集成测试：完整流程测试
3. ✅ 性能优化：模板缓存、Embedding 检索优化
4. ✅ 兼容性测试：多数据库测试
5. ✅ 前端集成测试：AntV 图表渲染测试
6. ✅ 文档更新

**预估工作量**: 3-4 天

## 四、关键技术点与注意事项

### 4.1 pgvector 支持

SQLBot 使用 pgvector 存储 Embedding。需要检查当前项目：
- ✅ 是否已安装 `pgvector` 扩展
- ✅ 是否已有 Embedding 计算逻辑
- ✅ 是否需要新增表结构 Embedding 存储表

**解决方案**:
- 如果已有 pgvector：直接使用
- 如果未安装：需要新增 pgvector 支持，或使用其他向量存储方案

### 4.2 模板变量替换

SQLBot 的模板使用 Python `format()` 方法替换变量，需要注意：
- 转义 `{` 和 `}` 使用 `{{` 和 `}}`
- 变量名需保持一致：`{engine}`, `{schema}`, `{question}` 等

### 4.3 LangGraph vs 函数式调用

SQLBot 使用函数式调用，当前项目使用 LangGraph。迁移时：
- 保持 LangGraph 架构
- 将 SQLBot 的函数封装为 LangGraph 节点
- 状态管理通过 `AgentState` 传递

### 4.4 前端 AntV 组件适配

需要确保前端支持：
- 动态图表配置解析
- 所有图表类型渲染（column、bar、line、pie、table）
- 数据格式转换（SQL 结果 → AntV 数据格式）

### 4.5 现有功能复用

**必须复用**:
- ✅ `services/datasource_service.py` - 数据源管理
- ✅ `services/user_service.py` - 用户管理
- ✅ `services/permission_service.py` - 权限管理
- ✅ `services/terminology_service.py` - 术语管理
- ✅ `services/data_training_service.py` - 数据训练示例

**需要增强**:
- 🔄 Embedding 检索能力（表结构、术语、示例）
- 🔄 权限规则格式化（转换为 SQL 过滤条件）

## 五、风险与挑战

### 5.1 技术风险

1. **pgvector 支持**
   - 风险：当前项目可能未安装 pgvector
   - 应对：评估替代方案（如使用 Milvus、Qdrant 等）

2. **模板系统复杂度**
   - 风险：YAML 模板变量多，替换逻辑复杂
   - 应对：充分测试，编写单元测试

3. **LangGraph 适配**
   - 风险：SQLBot 函数式调用转 LangGraph 节点可能有状态传递问题
   - 应对：仔细设计状态传递，充分测试

### 5.2 业务风险

1. **功能差异**
   - 风险：SQLBot 某些功能在当前项目中无对应实现
   - 应对：明确功能边界，确定哪些功能必须迁移，哪些可延后

2. **性能影响**
   - 风险：RAG 检索、多个 LLM 调用可能影响性能
   - 应对：优化缓存策略，异步处理，性能测试

### 5.3 兼容性风险

1. **数据库支持**
   - 风险：11 种数据库规则可能不完全兼容
   - 应对：逐个测试，逐步迁移

2. **前端兼容性**
   - 风险：AntV 组件可能不支持所有图表类型
   - 应对：提前验证，必要时使用替代方案

## 六、迁移时间估算

| 阶段 | 任务 | 预估时间 | 优先级 |
|------|------|----------|--------|
| 阶段一 | 模板系统迁移 | 3-4 天 | 🔴 最高 |
| 阶段二 | RAG 增强检索 | 2-3 天 | 🟡 高 |
| 阶段三 | 权限处理 | 2 天 | 🟡 高 |
| 阶段四 | 图表生成 | 3-4 天 | 🟡 高 |
| 阶段五 | 数据源选择与推荐 | 2 天 | 🟢 低 |
| 阶段六 | 动态 SQL（可选） | 2-3 天 | 🔵 低 |
| 阶段七 | 测试与优化 | 3-4 天 | 🟡 高 |
| **总计** | | **17-22 天** | |

**建议**:
- 优先完成阶段一、二、三、四（核心功能）
- 阶段五、六可根据需求延后
- 阶段七必须完成

## 七、迁移检查清单

### 模板系统 ✅
- [ ] 迁移 `template.yaml` 基础模板
- [ ] 迁移所有 11 种数据库 `sql_examples/*.yaml`
- [ ] 实现 `TemplateLoader` 类
- [ ] 实现 `PromptBuilder` 类
- [ ] SQL 生成节点使用模板系统
- [ ] 图表配置生成使用模板系统
- [ ] 权限过滤使用模板系统
- [ ] 数据源选择使用模板系统
- [ ] 推荐问题使用模板系统

### RAG 检索 ✅
- [ ] 表结构 Embedding 检索
- [ ] 术语库检索（复用现有服务）
- [ ] 训练示例检索（复用现有服务）
- [ ] RAG 增强节点集成

### 权限处理 ✅
- [ ] 权限规则获取（复用现有服务）
- [ ] 权限条件注入节点
- [ ] 行级权限支持
- [ ] 列级权限支持

### 图表生成 ✅
- [ ] 图表配置生成节点
- [ ] AntV 前端组件适配
- [ ] 支持所有图表类型
- [ ] 数据格式转换

### LangGraph 集成 ✅
- [ ] 状态图扩展
- [ ] AgentState 扩展
- [ ] 所有节点集成
- [ ] 流程测试

### 测试 ✅
- [ ] 单元测试
- [ ] 集成测试
- [ ] 多数据库测试
- [ ] 前端集成测试
- [ ] 性能测试

## 八、下一步行动

### 立即执行（阶段一）

1. **创建目录结构**
   ```bash
   mkdir -p agent/text2sql/template/yaml/sql_examples
   ```

2. **复制模板文件**
   - 从 SQLBot 复制 `template.yaml` 到 `agent/text2sql/template/yaml/`
   - 复制所有 `sql_examples/*.yaml` 文件

3. **实现模板加载器**
   - 编写 `TemplateLoader` 类
   - 实现缓存机制

4. **实现提示词构建器**
   - 编写 `PromptBuilder` 类
   - 支持所有模板模块

5. **重写 SQL 生成节点**
   - 使用模板系统
   - 测试 SQL 生成功能

### 等待确认

✅ **已确认事项**:

1. ✅ **pgvector 支持**: 已安装，可以直接使用
2. ✅ **前端 AntV 组件**: 未安装，需要在阶段四新增支持动态图表配置渲染
3. ✅ **迁移优先级**: 可自行决定，将优先完成阶段一、二、三、四（核心功能）
4. ✅ **测试环境**: 将创建 docker-compose 集成多种数据库并初始化测试数据库和脚本

---

**报告生成时间**: 2026-01-08  
**报告版本**: v1.1  
**状态**: ✅ 已确认，开始执行迁移

