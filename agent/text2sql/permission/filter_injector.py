"""
权限过滤注入节点
使用 LLM 将权限条件注入到 SQL 语句中
"""

import json
import logging
import traceback
from typing import Dict, Any, Optional

from langchain_core.messages import SystemMessage, HumanMessage

from agent.text2sql.state.agent_state import AgentState
from agent.text2sql.permission.permission_retriever import get_user_permission_filters
from agent.text2sql.template.prompt_builder import PromptBuilder
from agent.text2sql.template.schema_formatter import get_database_engine_info
from common.llm_util import get_llm
from services.datasource_service import DatasourceService
from model.db_connection_pool import get_db_pool

logger = logging.getLogger(__name__)
pool = get_db_pool()


def permission_filter_injector(state: AgentState) -> AgentState:
    """
    权限过滤注入节点
    1. 获取用户的权限过滤条件
    2. 使用 LLM 将权限条件注入 SQL
    3. 返回过滤后的 SQL
    
    Args:
        state: Agent 状态对象
        
    Returns:
        更新后的 state
    """
    try:
        # 获取生成的SQL
        generated_sql = state.get("generated_sql")
        if not generated_sql or generated_sql == "No SQL query generated":
            logger.warning("没有生成的SQL，跳过权限过滤")
            return state
        
        # 获取数据源ID和用户ID
        datasource_id = state.get("datasource_id")
        user_id = state.get("user_id", 1)  # 默认为管理员
        
        if not datasource_id:
            logger.warning("没有数据源ID，跳过权限过滤")
            return state
        
        # 获取数据源信息
        with pool.get_session() as session:
            datasource = DatasourceService.get_datasource_by_id(session, datasource_id)
            if not datasource:
                logger.warning(f"数据源不存在: {datasource_id}")
                return state
            
            db_type = datasource.type or "mysql"
        
        # 获取数据库引擎信息
        engine = get_database_engine_info(db_type)
        
        # 获取权限过滤条件
        # 注意：这里我们简化处理，从SQL中提取表名
        # 实际应用中，可以从 state 中获取表名列表
        table_names = None  # 如果为None，则获取所有表的权限
        filters = get_user_permission_filters(
            datasource_id=datasource_id,
            user_id=user_id,
            table_names=table_names,
        )
        
        # 如果没有权限过滤条件，直接返回
        if not filters:
            logger.info("没有权限过滤条件，直接返回原始SQL")
            state["filtered_sql"] = generated_sql
            return state
        
        # 使用 PromptBuilder 构建权限过滤提示词
        prompt_builder = PromptBuilder()
        
        system_prompt, user_prompt = prompt_builder.build_permission_prompt(
            sql=generated_sql,
            filters=filters,
            engine=engine,
            lang="简体中文",
        )
        
        # 构建消息列表
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        
        # 调用 LLM
        llm = get_llm(0)
        response = llm.invoke(messages)
        
        # 解析响应（JSON 格式）
        response_content = response.content.strip()
        
        # 清理 JSON 字符串（移除可能的 markdown 代码块标记）
        if "```json" in response_content:
            response_content = response_content.split("```json")[1]
        if "```" in response_content:
            response_content = response_content.split("```")[0]
        response_content = response_content.strip()
        
        # 解析 JSON
        try:
            result = json.loads(response_content)
            
            if result.get("success", True):
                filtered_sql = result.get("sql", generated_sql)
                state["filtered_sql"] = filtered_sql
                logger.info(f"权限过滤成功，原始SQL: {generated_sql[:100]}...")
                logger.info(f"过滤后SQL: {filtered_sql[:100]}...")
            else:
                error_message = result.get("message", "无法注入权限过滤条件")
                logger.warning(f"权限过滤失败: {error_message}")
                # 如果权限过滤失败，使用原始SQL
                state["filtered_sql"] = generated_sql
                
        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 响应 JSON 失败: {e}")
            logger.error(f"响应内容: {response_content[:500]}")
            # 如果解析失败，使用原始SQL
            state["filtered_sql"] = generated_sql
        
    except Exception as e:
        traceback.print_exception(e)
        logger.error(f"权限过滤注入过程中发生错误: {e}", exc_info=True)
        # 如果发生错误，使用原始SQL
        state["filtered_sql"] = state.get("generated_sql", "No SQL query generated")
    
    return state

